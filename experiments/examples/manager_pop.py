#!/usr/bin/env python3
import os
import sys
import asyncio

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
sys.path.append(newpath)

from pygazebo.pygazebo import DisconnectError

from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.tol.manage import World

def dummy_selection(individuals):
    return individuals[-1]


def crossover_selection(individuals, selector, howmany:int):
    selected = []
    for i in range(howmany):
        selected.append(
            selector(individuals)
        )
    return selected


async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    num_generations = 10

    genotype_conf = PlasticodingConfig(
        max_structural_modules=10
    )

    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=genotype_conf,
    )

    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
    )

    settings = parser.parse_args()
    exp_management = ExperimentManagement(settings)

    if not exp_management.experiment_is_new() and settings.recovery_enabled:
        recovery_state = exp_management.read_recovery_state()
        gen_num = int(recovery_state[0])
        next_robot_id = int(recovery_state[1])
    else:
        gen_num = 0
        next_robot_id = 0

    population_conf = PopulationConfig(
        population_size=10,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function=fitness.random,
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        crossover_conf=crossover_conf,
        selection=dummy_selection,
        parent_selection=lambda individuals: crossover_selection(individuals, dummy_selection, 2),
        population_management=steady_state_population_management,
        population_management_selector=dummy_selection,
        evaluation_time=1,
        experiment_name=settings.experiment_name,
        exp_management=exp_management,
        settings=settings,
        offspring_size=2
    )

    simulator_connection = await World.create(settings)

    population = Population(population_conf, simulator_connection, next_robot_id)

    if not exp_management.experiment_is_new() and settings.recovery_enabled:
        population.load_pop(gen_num)
    else:
        exp_management.create_exp_folders()
        await population.init_pop()
        exp_management.export_snapshots(population.individuals, gen_num)

    while gen_num < num_generations:
        gen_num += 1
        population = await population.next_gen(gen_num)
        exp_management.export_snapshots(population.individuals, gen_num)
        exp_management.update_recovery_state(gen_num, population.next_robot_id)

    # output result after completing all generations...


def main():
    def handler(loop, context):
        exc = context['exception']
        if isinstance(exc, DisconnectError) \
                or isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            sys.exit(0)
        raise context['exception']

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handler)
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Got CtrlC, shutting down.")


if __name__ == '__main__':
    print("STARTING")
    main()
    print("FINISHED")
