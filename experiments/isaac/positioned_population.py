from __future__ import annotations

from typing import Optional, List, AnyStr, Tuple

import math
import random
import enum
from dataclasses import dataclass

from pyrevolve import SDF
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue


@enum.unique
class SpawnStrategy(enum.Enum):
    SINGLE_MOTHER_OFFSPRING = enum.auto()
    SQUARE_AREA = enum.auto()
    MOTHER_LOCATION = enum.auto()


@dataclass
class SpawnArea:
    """
    Spawn area class (box representation)
    coordinates are for a corner, not at the center of the box
    """
    x: float
    y: float
    width: float
    height: float

    def __mul__(self, other: float) -> SpawnArea:
        assert type(other) is float or type(other) is int
        return SpawnArea(self.x, self.y, self.width*other, self.height*other)


class PositionedPopulation(Population):
    ROBOT_RADIUS = 2.0
    SURVIVAL_SELECTION = 'RANKING_BASED'

    def __init__(self,
                 config: PopulationConfig,
                 simulator_queue: SimulatorQueue,
                 analyzer_queue: Optional[AnalyzerQueue] = None,
                 next_robot_id: int = 1,
                 grid_cell_size: float = 0.5,
                 spawn_area: SpawnArea = None,
                 spawn_location_method: SpawnStrategy = SpawnStrategy.MOTHER_LOCATION):
        super().__init__(config, simulator_queue, analyzer_queue, next_robot_id)
        self.grid_cell_size: float = grid_cell_size
        self.spawn_location_method: SpawnStrategy = spawn_location_method
        area_size: float = math.floor(math.sqrt(config.population_size))
        self.spawn_area: SpawnArea = spawn_area
        if spawn_area is None:
            self.spawn_area = SpawnArea(0.0, 0.0, 1.0, 1.0) * area_size * self.grid_cell_size

    def _new_individual(self,
                        genotype,
                        parents: Optional[Tuple[Individual] | Tuple[Individual, Individual] | List[Individual]] = None,
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

    def _grid_positioning(self, n_individuals):
        sqrt_pop: float = math.floor(math.sqrt(n_individuals))
        r_width = self.spawn_area.width / sqrt_pop
        r_height = self.spawn_area.height / sqrt_pop
        for i in range(n_individuals):
            x: float = (i // sqrt_pop) * r_width
            y: float = (i % sqrt_pop) * r_height
            pose = SDF.math.Vector3(x, y, 0)
            yield pose

    async def initialize(self, recovered_individuals: Optional[List[Individual]] = None) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals
        n_new_individuals = self.config.population_size-len(recovered_individuals)

        # TODO there are recovery problems here,
        # but I will ignore them (recovered robots and new robots positions are initialized independently)
        for i, pose in enumerate(self._grid_positioning(n_new_individuals)):
            print(f"####### Creating robot {i} at pose {pose} - {self.spawn_area}")
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
        for i, (individual, pose) in enumerate(zip(self.individuals, self._grid_positioning(len(self.individuals)))):
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
        for pose in self._grid_positioning(n_new_individuals):
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
                              gen_num: int,
                              recovered_individuals: Optional[List[Individual]] = None) -> PositionedPopulation:
        assert recovered_individuals is None
        if self.spawn_location_method == SpawnStrategy.SINGLE_MOTHER_OFFSPRING:
            return await self.next_generation_one_offspring(gen_num)
        elif self.spawn_location_method == SpawnStrategy.MOTHER_LOCATION \
                or self.spawn_location_method == SpawnStrategy.SQUARE_AREA:
            return await self.next_generation_steadystate(gen_num)
        else:
            raise RuntimeError("Spawn Strategy not found")

    async def next_generation_steadystate(self, gen_num: int) -> PositionedPopulation:
        # rank individuals based on fitness, high to low
        from operator import attrgetter
        survivors = sorted(self.individuals, key=attrgetter('fitness'), reverse=True)

        if self.SURVIVAL_SELECTION == 'RANKING_BASED':
            # remove the lower (fitness) half of the population
            survival_cutoff = len(self.individuals)//4
            survivors = survivors[:survival_cutoff]
        elif self.SURVIVAL_SELECTION == 'AVG_FITNESS':
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
                    next_robot_id = self.next_robot_id
                    if self.spawn_location_method == SpawnStrategy.MOTHER_LOCATION:
                        offspring = self.attempt_new_individual_with_placement(next_robot_id,
                                                                               parent,
                                                                               population_alive=offsprings+survivors,
                                                                               offspring_range=offspring_range)
                    elif self.spawn_location_method == SpawnStrategy.SQUARE_AREA:
                        spawn_area: SpawnArea = self.spawn_area*(offspring_range/3.0)
                        offspring = self.attempt_new_individual_random_placement(next_robot_id,
                                                                                 parent,
                                                                                 population_alive=offsprings+survivors,
                                                                                 offspring_spawn_area=spawn_area)
                    else:
                        raise RuntimeError(f'Spawn strategy "{self.spawn_location_method}" not found')
                    if offspring is not None:
                        # new offspring generated!
                        self.next_robot_id += 1
                        offsprings.append(offspring)
                        new_population_size += 1
                        allocated_offspring[i] -= 1

            # maybe not done yet, prepare for next loop with increased range (linear increase)
            offspring_range *= 2

        # Individual.clone() seems to have issues with the pose of the robot, resetting it to (0,0,0)
        # new_individuals: List[Individual] = [i.clone() for i in survivors] + offsprings
        new_individuals: List[Individual] = survivors + offsprings
        assert len(self.individuals) == len(new_individuals)

        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)

        # create next population
        new_population = PositionedPopulation(self.config,
                                              self.simulator_queue,
                                              self.analyzer_queue,
                                              self.next_robot_id,
                                              self.grid_cell_size,
                                              self.spawn_area,
                                              self.spawn_location_method)
        new_population.individuals = new_individuals
        logger.info(f"new generation({gen_num} created")
        return new_population

    def attempt_new_individual_with_placement(self,
                                              new_robot_id,
                                              mother: Individual,
                                              population_alive: List[Individual],
                                              offspring_range: float = 2.0) -> Optional[Individual]:
        """
        Attempt to generate offspring from mother (and its internal list)

        if generated genotype is not viable, return None
        if generated offspring has no space were to be generated (using population_alive to test), return None
        if a position around the mother is not found, a new attempt to reproduce is made with a double range.
        Range is doubled until all allocated offspring are generated.

        :param new_robot_id: id of the new robot
        :param mother: offspring parent
        :param population_alive: individuals that are already alive (never place robots too close to each other)
        :param offspring_range: range around the mother were to place the new offspring
        :return: new individual if possible
        """
        # find pose
        suggested_pose: SDF.math.Vector3
        # Test 100 random location
        for _ in range(100):
            random_direction = SDF.math.Vector3(random.random(), random.random(), 0)
            random_direction.normalize()
            suggested_pose = mother.pose + random_direction * offspring_range * random.random()
            # Test random location against the robots already alive
            for i_alive in population_alive:
                distance: SDF.math.Vector3 = i_alive.pose - suggested_pose
                distance.z = 0
                if distance.magnitude() < self.ROBOT_RADIUS*2:
                    # One conflict found
                    break
            else:
                # Location Found!
                break
            # if you are here, one conflict was found, try again with another random pose
        else:
            logger.info(f'Mother:{mother} failed to find empty spot to generate new individual. Skipping to next potential parent')
            return None

        return self._attempt_new_individual(new_robot_id, mother, suggested_pose)

    def attempt_new_individual_random_placement(self,
                                                new_robot_id,
                                                mother: Individual,
                                                population_alive: List[Individual],
                                                offspring_spawn_area: SpawnArea) -> Optional[Individual]:
        """
        Attempt to generate offspring from mother (and its internal list)

        if generated genotype is not viable, return None
        if generated offspring has no place were to be generated (using population_alive to test), return None
        :param new_robot_id: id of the new robot
        :param mother: parent
        :param population_alive: individuals that are already alive (never place robots too close to each other)
        :param offspring_spawn_area: area were to place the new offspring
        :return: new individual if possible
        """
        # find pose
        random_position: SDF.math.Vector3
        # Test 100 random location
        for _ in range(100):
            x = offspring_spawn_area.x + (offspring_spawn_area.width * random.random())
            y = offspring_spawn_area.y + (offspring_spawn_area.height * random.random())
            random_position = SDF.math.Vector3(x, y, 0)
            # Test random location against the robots already alive
            for i_alive in population_alive:
                distance: SDF.math.Vector3 = i_alive.pose - random_position
                distance.z = 0
                if distance.magnitude() < self.ROBOT_RADIUS*2:
                    # One conflict found
                    break
            else:
                # Location Found!
                break
            # if you are here, one conflict was found, try again with another random pose
        else:
            logger.info(f'Mother:{mother} failed to find empty spot to generate new individual. Skipping to next potential parent')
            return None

        return self._attempt_new_individual(new_robot_id, mother, random_position)

    def _attempt_new_individual(self,
                                new_robot_id,
                                mother: Individual,
                                pose: SDF.math.Vector3) -> Optional[Individual]:
        """
        Creates a new individual
        :param new_robot_id: id of the new robot
        :param mother: parent
        :param pose: pose of the new individual
        :return: new individual if possible
        """
        # Selection operator (based on fitness perceived by the individuals)
        if len(mother.candidate_partners) > 0:
            father: Optional[Individual] = self.config.selection(mother.candidate_partners)
            parents = (mother, father)
            child_genotype = self.config.crossover_operator(parents, self.config.genotype_conf, self.config.crossover_conf)
            child = Individual(child_genotype)
        else:
            father = None
            child = mother
            parents = (mother,)
        child.parents = parents
        child.genotype.id = new_robot_id

        # Attempt to make new genome that is viable
        N_MUTATION_ATTEMPTS = 10
        for j in range(N_MUTATION_ATTEMPTS):
            # Mutation operator
            child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)

            if self.config.genotype_test(child_genotype):
                # valid individual found, exit infinite loop
                # Insert individual in new population
                child = self._new_individual(child_genotype, parents, pose)
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
                                              self.grid_cell_size,
                                              self.spawn_area,
                                              self.spawn_location_method)
        new_population.individuals = new_individuals
        logger.info(f"new generation({gen_num} created")
        return new_population
