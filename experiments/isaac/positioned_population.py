from __future__ import annotations

from typing import Optional, List, AnyStr

import math
import random

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
                        pose: Optional[SDF.math.Vector3] = None) -> Individual:
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
            print(f"####### Creating robot {i} at pose {pose} - {area_size}")
            new_genotype = self.config.genotype_constructor(self.config.genotype_conf, self.next_robot_id)
            individual = self._new_individual(new_genotype, pose=pose)
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)
        self.individuals = recovered_individuals + self.individuals

    async def initialize_from_previous_population(self, data_path: AnyStr, gen_num: int) -> None:
        """
        Populates the population (individuals list) with Individuals from the previous population
        """
        n_new_individuals = self.load_external_snapshot(data_path, gen_num, multi_development=True)
        print(f"Loaded {n_new_individuals} individuals from snapshot")

        # TODO there are recovery problems here,
        # but I will ignore them (recovered robots and new robots positions are initialized independently)
        area_size: float = math.floor(math.sqrt(n_new_individuals))
        for i, individual in enumerate(self.individuals):
            x: float = i % area_size
            y: float = i // area_size
            pose = SDF.math.Vector3(x, y, 0) * self.grid_cell_size
            print(f"####### Creating robot {i} at pose {pose} - {area_size}")
            individual.pose = pose
            individual.phenotype.pose = pose

        await self.evaluate(self.individuals, 0)

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

    async def next_generation(self, gen_num: int) -> PositionedPopulation:
        # rank individuals based on fitness, high to low
        from operator import attrgetter
        survivors = sorted(self.individuals, key=attrgetter('fitness'), reverse=True)

        SURVIVAL_SELECTION = 'RANKING_BASED'
        if SURVIVAL_SELECTION == 'RANKING_BASED':
            # remove the lower (fitness) half of the population
            survival_cutoff = len(self.individuals)//4
            survivors = [i.clone() for i in survivors[:survival_cutoff]]
        elif SURVIVAL_SELECTION == 'AVG_FITNESS':
            average_fitness = 0.0
            for individual in self.individuals:
                assert individual.fitness is not None
                average_fitness += individual.fitness
            average_fitness /= len(self.individuals)

            new_survivors = []
            # kill bad individuals
            for individual in self.individuals:
                if individual >= average_fitness:
                    new_survivors.append(individual.clone())
            survivors = new_survivors

        assert len(survivors) < len(self.individuals)

        # generate new population
        offsprings = []
        new_population_size = len(survivors)
        offspring_range: float = 3.0
        missing_offpsring = len(self.individuals) - new_population_size
        # 5 to first, 1 to last, linear scaling (y=-x/4 + 5), 75 offspring total
        allocated_offspring = [int(round((-i/5.99)+5)) for i in range(len(survivors))]
        # 7 to first, because of approximation errors
        allocated_offspring[0] += missing_offpsring - sum(allocated_offspring)
        assert sum(allocated_offspring) == missing_offpsring

        while new_population_size < len(self.individuals):
            # individuals are sorted high -> low
            for i, (parent, n_offspring) in enumerate(zip(survivors, allocated_offspring)):
                for _ in range(n_offspring):
                    offspring = self.attempt_new_individual_with_placement(parent,
                                                                           population_alive=offsprings+survivors,
                                                                           offspring_range=offspring_range)
                    if offspring is not None:
                        # new offspring generated!
                        offspring.genotype.id = self.next_robot_id
                        self.next_robot_id += 1
                        offsprings.append(offspring)
                        new_population_size += 1
                        allocated_offspring[i] -= 1

            # maybe not done yet, prepare for next loop with increased range (linear increase)
            offspring_range *= 2

        new_individuals: List[Individual] = survivors + offsprings
        assert len(self.individuals) == len(new_individuals)

        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)

        # create next population
        new_population = PositionedPopulation(self.config,
                                              self.simulator_queue,
                                              self.analyzer_queue,
                                              self.next_robot_id,
                                              self.grid_cell_size)
        new_population.individuals = new_individuals
        logger.info(f"new generation({gen_num} created")
        return new_population

    def attempt_new_individual_with_placement(self,
                                              mother: Individual,
                                              population_alive: List[Individual],
                                              offspring_range: float = 2.0) -> Optional[Individual]:
        """
        Attempt to generate offspring from mother (and its internal list)

        if generated genotype is not viable, return None
        if generated offspring has no space were to be generated (using population_alive to test), return None
        """
        mother_candidates = [candidate for candidate in mother.candidate_partners]

        # find pose
        ROBOT_RADIUS = 2.0
        suggested_pose: SDF.math.Vector3
        # Test 100 random location
        for _ in range(100):
            random_direction = SDF.math.Vector3(random.random(), random.random(), random.random())
            random_direction.normalize()
            suggested_pose = mother.pose + random_direction * offspring_range * random.random()
            # Test random location against the robots already alive
            for i_alive in population_alive:
                distance: SDF.math.Vector3 = i_alive.pose - suggested_pose
                if distance.magnitude() < ROBOT_RADIUS*2:
                    # One conflict found
                    break
            else:
                # Location Found!
                break
            # if you are here, one conflict was found, try again with another random pose
        else:
            logger.info(f'Mother:{mother} failed to find empty spot to generate new individual. Skipping to next potential parent')
            return None

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
        child.genotype.id = self.next_robot_id

        # Attempt to make new genome that is viable
        N_MUTATION_ATTEMPTS = 10
        for j in range(N_MUTATION_ATTEMPTS):
            # Mutation operator
            child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)

            if self.config.genotype_test(child_genotype):
                # valid individual found, exit infinite loop
                # Insert individual in new population
                child = self._new_individual(child_genotype, parents, suggested_pose)
                return child
        # Candidate individual not found after 10 random mutations
        # this crossover does not work: remove father from candidate list
        logger.info(f'Mother:{mother} failed to generate valid offspring in {N_MUTATION_ATTEMPTS} mutation attempts. Skipping to next potential parent')
        return None

    async def next_generation_one_offspring(self, gen_num: int) -> PositionedPopulation:
        """
        Generate new generation where every individual is replaced by its offspring (as mother).
        Every individual can be father multiple times.
        """
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
                    logger.info(f'Mother:{mother} failed to generate valid offspring in 100 mutation attempts '
                                f'- removing Father:"{father}" from list:{mother_candidates}')
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
