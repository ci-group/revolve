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
from pyrevolve.evolution import fitness
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.evolution.selection import multiple_selection, tournament_selection


class ExperimentConfig:
    def __init__(self):

        self.num_generations = 100

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
            population_size=100,
            genotype_constructor=random_initialization,
            genotype_conf=self.genotype_conf,
            fitness_function=fitness.online_old_revolve,
            mutation_operator=standard_mutation,
            mutation_conf=self.mutation_conf,
            crossover_operator=standard_crossover,
            crossover_conf=self.crossover_conf,
            selection=lambda individuals: tournament_selection(individuals, 2),
            parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
            population_management=steady_state_population_management,
            population_management_selector=tournament_selection,
            evaluation_time=30,
            offspring_size=50,
        )


async def run():
    """
    The main coroutine, which is started below.
    """

    experiment_conf = ExperimentConfig()
    settings = parser.parse_args()
    simulator_supervisor = DynamicSimSupervisor(
        world_file=newpath + "/" + settings.world,
        simulator_cmd=settings.simulator_cmd,
        simulator_args=["--verbose"],
        plugins_dir_path=os.path.join(newpath, 'build', 'lib'),
        models_dir_path=os.path.join(newpath, 'models')
    )

    simulator_supervisor.launch_simulator(port=11345)

    population = Population(experiment_conf.population_conf,
                            await World.create(settings, world_address=("127.0.0.1", 11345)))
    await population.init_pop()
    population.simulator_connection.disconnect()

    simulator_supervisor.relaunch()

    population.simulator_connection = await World.create(settings, world_address=("127.0.0.1", 11345))

    gen_num = 0
    while gen_num < experiment_conf.num_generations:
        population = await population.next_gen(gen_num+1)
        population.simulator_connection.disconnect()
        simulator_supervisor.relaunch()
        population.simulator_connection = await World.create(settings)
        gen_num += 1

    # output result after completing all generations...
    simulator_supervisor.stop()


def main():
    def handler(_loop, context):
        try:
            exc = context['exception']
        except KeyError:
            print(context['message'])
            return

        if isinstance(exc, DisconnectError) \
                or isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            sys.exit(0)

        import traceback
        traceback.print_exc(exc)
        raise exc

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
