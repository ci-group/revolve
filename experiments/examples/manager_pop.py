#!/usr/bin/env python3
import os
import sys
import asyncio

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
sys.path.append(newpath)

from pygazebo.pygazebo import DisconnectError

from pyrevolve import revolve_bot
from pyrevolve import parser
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import World

from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.lsystem.mutation.mutation import MutationConfig
from pyrevolve.evolution.lsystem.mutation.standard_mutation import standard_mutation
from pyrevolve.evolution.lsystem.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.genotype import GenotypeConfig
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig


def dummy_selection(individuals):
    return individuals[0]

def crossover_selection(individuals, selector, howmany:int):
    selected = []
    for i in range(howmany):
        selected.append(
            # selector(individuals)
            individuals[i]
        )
    return selected

def steady_state_population_management(old_individuals, new_individuals, selector):
    pop_size = len(old_individuals)
    selection_pool = old_individuals + new_individuals # check this
    selected_individuals = []
    for _i in range(pop_size):
        selected = selector(selection_pool)
        selected_individuals.append(selected)

    return selected_individuals

async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    settings = parser.parse_args()

    num_generations = 5

    genotype_conf = PlasticodingConfig()

    mutation_conf = MutationConfig(
    mutation_prob=0.8,
    genotype_conf=genotype_conf,
    )

    population_conf = PopulationConfig(
        population_size=10,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        selection=dummy_selection,
        parent_selection=lambda individuals: crossover_selection(individuals, dummy_selection, 2),
        population_management=lambda old, new: steady_state_population_management(old, new, dummy_selection),
        offspring_size=5,
    )

    population = Population(population_conf)
    population.init_pop()
    await population.evaluate(population.individuals) # What to do after initialising because phenotypes and fitness will be NULL

    i = 0
    while i < num_generations:
        population.next_gen()
        i += 1

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
