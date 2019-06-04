#!/usr/bin/env python3
import asyncio
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
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.util.supervisor.simulator_simple_queue import SimulatorSimpleQueue


async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    num_generations = 100

    genotype_conf = PlasticodingConfig(
        max_structural_modules=20,
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
        population_size=100,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function=fitness.online_old_revolve,
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=30,
        offspring_size=50,
        experiment_name=settings.experiment_name,
        exp_management=exp_management,
        settings=settings,
    )

    settings = parser.parse_args()
    simulator_queue = SimulatorSimpleQueue(5, settings, port_start=11435)
    await simulator_queue.start()

    population = Population(population_conf, simulator_queue, next_robot_id)

    if not exp_management.experiment_is_new() and settings.recovery_enabled:
        # loading a previous state of the experiment
        population.load_pop(gen_num)
    else:
        # starting a new experiment
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
    import traceback

    def handler(_loop, context):
        try:
            exc = context['exception']
        except KeyError:
            print(context['message'])
            return

        if isinstance(exc, DisconnectError) \
                or isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            # sys.exit(0)

        if isinstance(exc, OSError) and exc.errno == 9:
            print(exc)
            traceback.print_exc()
            return

        traceback.print_exc()
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
