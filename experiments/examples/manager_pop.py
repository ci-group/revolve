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
    return individuals[0]


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
    num_generations = 1

    genotype_conf = PlasticodingConfig(
        max_structural_modules=10,
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

    population_conf = PopulationConfig(
        population_size=4,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
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
        offspring_size=1
    )

    simulator_connection = await World.create(settings)

    population = Population(population_conf, simulator_connection)
    gen_num = 0

    if exp_management.experiment_is_new:
        exp_management.create_exp_folders()
        await population.init_pop()
        exp_management.export_snapshots(population.individuals, gen_num)
    #else:
        # recover here soon!
     #   population = None
        # set gem num as recovered pop
     #   gen_num = 0
      #  population.evaluate(population.individuals, gen_num)

    while gen_num < num_generations:
        gen_num += 1
        population = await population.next_gen(gen_num)
        exp_management.export_snapshots(population.individuals, gen_num)
        
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
