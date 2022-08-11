from __future__ import annotations

from typing import Optional, List

import math

from pyrevolve import SDF
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue


class PositionedPopulation(Population):

    def __init__(self,
                 config: PopulationConfig,
                 simulator_queue: SimulatorQueue,
                 analyzer_queue: Optional[AnalyzerQueue] = None,
                 next_robot_id: int = 1,
                 grid_cell_size: float = 0.5):
        super().__init__(config, simulator_queue, analyzer_queue, next_robot_id)
        self.grid_cell_size: float = grid_cell_size

    def _new_individual(self,
                        genotype,
                        parents: Optional[List[Individual]] = None,
                        pose: Optional[SDF.math.Vector3] = None):
        if pose is None:
            assert parents is not None
            assert len(parents) > 0
            pose = parents[0].pose

        individual = Individual(genotype, pose=pose.copy())
        individual.develop()
        if isinstance(individual.phenotype, list):
            for alternative in individual.phenotype:
                alternative.update_substrate()
                alternative.measure_phenotype()
                alternative.export_phenotype_measurements(self.config.experiment_management.data_folder)
        else:
            individual.phenotype.update_substrate()
            individual.phenotype.measure_phenotype()
            individual.phenotype.export_phenotype_measurements(self.config.experiment_management.data_folder)
        if parents is not None:
            individual.parents = parents

        self.config.experiment_management.export_genotype(individual)
        self.config.experiment_management.export_phenotype(individual)
        self.config.experiment_management.export_phenotype_images(individual)

        return individual

    async def initialize(self, recovered_individuals: Optional[List[Individual]] = None) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals
        n_new_individuals = self.config.population_size-len(recovered_individuals)

        # TODO there are recovery problems here,
        # but I will ignore them (recovered robots and new robots positions are initialized independently)
        area_size: float = math.floor(math.sqrt(n_new_individuals))
        for i in range(n_new_individuals):
            x: float = i % area_size
            y: float = i // area_size
            pose = SDF.math.Vector3(x, y, 0) * self.grid_cell_size
            new_genotype = self.config.genotype_constructor(self.config.genotype_conf, self.next_robot_id)
            individual = self._new_individual(new_genotype, pose=pose)
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)
        self.individuals = recovered_individuals + self.individuals

    async def initialize_from_single_individual(self, progenitor: Optional[Individual] = None) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        All individuals are based on a single random individual (one progenitor for all solutions)
        """
        progenitor_genotype = None
        n_new_individuals = self.config.population_size
        area_size: float = math.sqrt(n_new_individuals)
        for i in range(n_new_individuals):
            x: float = math.floor(i % area_size)
            y: float = i // area_size
            pose = SDF.math.Vector3(x, y, 0) * self.grid_cell_size
            if progenitor_genotype is None:
                # first loop iteration
                if progenitor is None:
                    # generate random progenitor
                    progenitor_genotype = self.config.genotype_constructor(self.config.genotype_conf, self.next_robot_id)
                    progenitor = self._new_individual(progenitor_genotype, pose=pose)
                else:
                    # use the one provided as parameter
                    progenitor_genotype = progenitor.genotype
                individual = progenitor
            else:
                # all remaining loop iterations
                new_genotype = self.config.mutation_operator(progenitor_genotype, self.config.mutation_conf)
                new_genotype.id = self.next_robot_id
                individual = self._new_individual(new_genotype, [progenitor], pose=pose)
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)


    async def next_generation(self,
                              gen_num: int) -> PositionedPopulation:
        new_individuals = []

        assert self.config.offspring_size == len(self.individuals)
        for individual in self.individuals:
            next_robot_id = self.next_robot_id
            self.next_robot_id += 1
            found = False

            mother: Individual = individual
            mother_candidates = [candidate for candidate in mother.candidate_partners]

            for i in range(100):
                # Selection operator (based on fitness perceived by the individuals)
                if len(mother_candidates) > 0:
                    father: Optional[Individual] = self.config.selection(mother_candidates)
                    parents = (mother, father)
                    child_genotype = self.config.crossover_operator(parents, self.config.genotype_conf, self.config.crossover_conf)
                    child = Individual(child_genotype)
                else:
                    father = None
                    child = mother
                    parents = (mother,)
                child.parents = parents
                child.genotype.id = next_robot_id

                for j in range(100):
                    # Mutation operator
                    child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)

                    if self.config.genotype_test(child_genotype):
                        # valid individual found, exit infinite loop
                        # Insert individual in new population
                        individual = self._new_individual(child_genotype, parents, mother.pose)
                        new_individuals.append(individual)
                        found = True
                        break
                else:
                    # Candidate individual not found after 100 random mutations
                    # this crossover does not work: remove father from candidate list
                    logger.info(f'Mother:{mother} failed to generate valid offspring in 100 trials - removing Father:"{father}" from list:{mother_candidates}')
                    if len(mother_candidates) == 0:
                        raise RuntimeError("No father left to remove, crashing now :)")
                    assert father is not None
                    mother_candidates.remove(father)
                    assert not found

                if found:
                    break
            else:
                # genotype test not passed
                raise RuntimeError("New individual not found, crashing now :)")

        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)

        # create next population
        if self.config.population_management_selector is not None:
            new_individuals = self.config.population_management(self.individuals,
                                                                new_individuals,
                                                                self.config.population_management_selector)
        else:
            new_individuals = self.config.population_management(self.individuals,
                                                                new_individuals)

        new_population = PositionedPopulation(self.config,
                                              self.simulator_queue,
                                              self.analyzer_queue,
                                              self.next_robot_id,
                                              self.grid_cell_size)
        new_population.individuals = new_individuals
        logger.info(f"new generation({gen_num} created")
        return new_population
