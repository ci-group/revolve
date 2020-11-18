import copy
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


from pyrevolve.evolution.population import Population


def NSGA2(population_individuals, offspring, debug: bool = False):
    population_size = len(population_individuals)
    offspring_size = len(offspring)

    # Preparate the objectives as a matrix of individuals in the rows and fitnesses in the columns.
    objectives = np.zeros((population_size + offspring_size, max(1, len(population_individuals[0].objectives))))  # TODO fitnesses is 0

    # Fill the objectives with all individual from the population and offspring combined.
    all_individuals = copy.deepcopy(population_individuals)
    all_individuals.extend(offspring)
    for index, individual in enumerate(all_individuals):
        # Negative fitness due to minimum search, TODO can be changed to be a default maximization NSGA.
        objectives[index, :] = [-objective for objective in individual.objectives]

    # Perform the NSGA Algorithm
    front_no, max_front = nd_sort(objectives, np.inf)
    crowd_dis = crowding_distance(objectives, front_no)
    sorted_fronts = sort_fronts(objectives, front_no, crowd_dis)

    # Select the new individuals based on the population size, since they are sorted we can index them directly.
    new_individuals = [all_individuals[index] for index in sorted_fronts[:population_size]]
    discarded_individuals = [all_individuals[index] for index in sorted_fronts[population_size:]]

    if debug:
       _visualize(objectives, sorted_fronts, new_individuals, discarded_individuals)

    return new_individuals


def _visualize(objectives, sorted_fronts, new_individuals, discarded_population):
    number_of_fronts = len(sorted_fronts)
    colors = cm.rainbow(np.linspace(1, 0, number_of_fronts))
    ax = None

    if objectives.shape[1] == 3:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

    for index, front in enumerate(sorted_fronts):
        if objectives.shape[1] == 3:
            ax.scatter(objectives[front, 0], objectives[front, 1], objectives[front, 2], s=100,
                       color=colors[index])
        else:
            plt.scatter(-objectives[front, 0], -objectives[front, 1], s=50,
                        color=colors[index])

    for individual in new_individuals:
        plt.scatter(individual.fitness[0], individual.fitness[1], s=5, color='black')
    for individual in discarded_population:
        plt.scatter(individual.fitness[0], individual.fitness[1], s=5, color='white')


# adapted from https://github.com/ChengHust/NSGA-II/blob/master/nd_sort.py
def nd_sort(objectives, n_sort):
    """
    :rtype:
    :param n_sort:
    :param pop_obj: objective vectors
    :return: [FrontNo, MaxFNo]
    """
    number_of_individuals, number_of_objectives = np.shape(objectives)
    _, inverse_sorted_population = np.unique(objectives[:, 0], return_inverse=True)

    # sorted first objective from high to low
    index = objectives[:, 0].argsort()
    sorted_objectives = objectives[index, :]

    # Prepare inf front for each entry
    front_no = np.inf * np.ones(number_of_individuals, dtype=np.int)
    max_front: int = 0

    # While there are front numbers to assign, continue
    while np.sum(front_no < np.inf) < min(n_sort, len(inverse_sorted_population)):
        max_front += 1

        # for each individual in population
        for current_individual in range(number_of_individuals):
            # Check that its front number is not assigned yet.
            if front_no[current_individual] == np.inf:
                dominated = False

                # Count down from the individual index to the last one available.
                for other_individual in range(current_individual - 1, -1, -1):
                    # compare against others with the same front.
                    if front_no[other_individual] == max_front:

                        # for each objective that is dominating the other candidate
                        m = np.sum(sorted_objectives[current_individual, :] >= sorted_objectives[other_individual, :])
                        dominated = m == number_of_objectives
                        if dominated:
                            break

                # If it is not dominated, set the current front.
                if not dominated:
                    front_no[current_individual] = max_front

    return front_no[inverse_sorted_population], max_front


# adapted from https://github.com/ChengHust/NSGA-II/blob/master/crowding_distance.py
def crowding_distance(objectives, front_number):
    """
    The crowding distance of each Pareto front
    :param pop_obj: objective vectors
    :param front_no: front numbers
    :return: crowding distance
    """
    number_of_individuals, number_of_objectives = np.shape(objectives)  # todo x, y?
    crowd_dis = np.zeros(number_of_individuals)

    # Initialize fronts
    front = np.unique(front_number)
    fronts = front[front != np.inf]
    for f in range(len(fronts)):
        front = np.array([k for k in range(len(front_number)) if front_number[k] == fronts[f]])

        # Find bounds
        Fmax = objectives[front, :].max(0)
        Fmin = objectives[front, :].min(0)

        # For each objective sort the front
        for i in range(number_of_objectives):
            rank = np.argsort(objectives[front, i])

            # Initialize Crowding distance
            crowd_dis[front[rank[0]]] = np.inf
            crowd_dis[front[rank[-1]]] = np.inf

            for j in range(1, len(front) - 1):
                crowd_dis[front[rank[j]]] += (objectives[(front[rank[j + 1]], i)] -
                                              objectives[(front[rank[j - 1]], i)]) / (Fmax[i] - Fmin[i])
    return crowd_dis


def sort_fronts(objectives, front_no, crowd_dis):
    front_dict = dict() # dictionary indexed by front number inserting objective with crowd distance as tuple

    for objective_index in range(len(objectives)):
        if front_no[objective_index] not in front_dict.keys():
            front_dict[front_no[objective_index]] = [(crowd_dis[objective_index], objective_index)]
        else:
            front_dict[front_no[objective_index]].append((crowd_dis[objective_index], objective_index))

    sorted_fronts = []
    sorted_keys = sorted(front_dict.keys())

    for key in sorted_keys:
        front_dict[key].sort(key=lambda x: x[0], reverse=True)
        for element in front_dict[key]:
            sorted_fronts.append(element[1])

    return sorted_fronts


if __name__ == "__main__":
    from pyrevolve import parser
    from pyrevolve.evolution import fitness
    from pyrevolve.evolution.selection import multiple_selection, tournament_selection
    from pyrevolve.evolution.population import Population, PopulationConfig
    from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
    from pyrevolve.experiment_management import ExperimentManagement
    from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
    from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
    from pyrevolve.genotype.plasticoding.initialization import random_initialization
    from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
    from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
    from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
    from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
    from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
    from pyrevolve.custom_logging.logger import logger

    # experiment params #
    num_generations = 100
    population_size = 10
    offspring_size = 10

    genotype_conf = PlasticodingConfig(
        max_structural_modules=20,
        max_joints=10,
    )

    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=genotype_conf,
    )

    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
    )
    # experiment params #

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info('Activated run ' + settings.run + ' of experiment ' + settings.experiment_name)

    gen_num = 0
    next_robot_id = 1

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity,
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        crossover_conf=crossover_conf,

        selection=lambda individuals: tournament_selection(individuals, 4),
        parent_selection=lambda individuals: multiple_selection(individuals, 4, tournament_selection),

        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
    )

    n_cores = settings.n_cores

    settings = parser.parse_args()
    simulator_queue = SimulatorQueue(n_cores, settings, settings.port_start)

    analyzer_queue = AnalyzerQueue(1, settings, settings.port_start + n_cores)

    population = Population(population_conf, simulator_queue, analyzer_queue, next_robot_id)
    population.init_pop()

    population2 = Population(population_conf, simulator_queue, analyzer_queue, next_robot_id)
    population2.init_pop()

    offspring = population2.individuals

    def initialize_fitness(individuals):
        d3_enabled: bool = False
        for individual in individuals:
            theta = np.random.uniform(0, math.pi/2)
            omega = np.random.uniform(0, math.pi/2)
            r = np.random.uniform(0.5, 1)
            if d3_enabled:
                individual.fitness = [r * np.cos(theta) * np.cos(omega), r * np.sin(theta), r * np.cos(theta) * np.sin(omega)]
            else:
                individual.fitness = [r * np.cos(theta), r * np.sin(theta)]

    initialize_fitness(population.individuals)
    initialize_fitness(offspring)

    survived_individuals = NSGA2(population, offspring, debug=True)

    plt.show()
