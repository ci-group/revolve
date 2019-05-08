#!/usr/bin/env python3
import os
import sys
import asyncio
import psutil

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
relative = os.path.join(current_dir,__file__)
sys.path.append(newpath)

from pygazebo.pygazebo import DisconnectError

from pyrevolve import parser
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import Supervisor
from multiprocessing import Process

def dummy_selection(individuals):
    return individuals[0]


def crossover_selection(individuals, selector, howmany:int):
    selected = []
    for i in range(howmany):
        selected.append(
            selector(individuals)
        )
    return selected


class ExperimentConfig:
    def __init__(self):

        self.num_generations = 10

        self.genotype_conf = PlasticodingConfig(
            max_structural_modules=20,
        )
        self.mutation_conf = MutationConfig(
            mutation_prob=0.8,
            genotype_conf=self.genotype_conf,
        )

        self.crossover_conf = CrossoverConfig(
            crossover_prob=0.8,
        )

        self.population_conf = PopulationConfig(
            population_size=6,
            genotype_constructor=random_initialization,
            genotype_conf=self.genotype_conf,
            mutation_operator=standard_mutation,
            mutation_conf=self.mutation_conf,
            crossover_operator=standard_crossover,
            crossover_conf=self.crossover_conf,
            selection=dummy_selection,
            parent_selection=lambda individuals: crossover_selection(individuals, dummy_selection, 2),
            population_management=steady_state_population_management,
            population_management_selector=dummy_selection,
            evaluation_time=30,
            offspring_size=3,
        )


async def run():
    """
    The main coroutine, which is started below.
    """

    experiment_conf = ExperimentConfig()
    settings = parser.parse_args()
    simulator_supervisor = Supervisor(
        world_file=newpath + "/" + settings.world,
        simulator_cmd=settings.simulator_cmd,
        simulator_args=["--verbose"],
        plugins_dir_path=os.path.join(newpath, 'build', 'lib'),
        models_dir_path=os.path.join(newpath, 'models')
    )
    simulator_supervisor._launch_simulator()
    simulator_connection = await World.create(settings)

    population = Population(experiment_conf.population_conf, simulator_connection)
    # await population.init_pop()
    population.simulator_connection.disconnect()
    await asyncio.wait_for(simulator_supervisor.relaunch(), None)
    aaa = World.create(settings)
    population.simulator_connection = await aaa

    gen_num = 0
    while gen_num < experiment_conf.num_generations:
        population = await population.next_gen(gen_num+1)
        await asyncio.wait_for(simulator_supervisor.relaunch(), None)
        aaa = World.create(settings)
        population.simulator_connection = await aaa
        gen_num += 1

    # output result after completing all generations...


def main():
    def handler(loop, context):
        exc = context['exception']
        import traceback
        traceback.print_exc()
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
