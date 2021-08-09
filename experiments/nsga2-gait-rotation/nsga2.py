from math import inf
from typing import List
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

from pyrevolve.evolution.individual import Individual


def NSGA2(population_individuals: List[Individual], offspring: List[Individual], debug: bool = False):
    population_size = len(population_individuals)
    offspring_size = len(offspring)
    # Preparate the objectives as a matrix of individuals in the rows and fitnesses in the columns.
    objectives = np.zeros(
        (population_size + offspring_size, max(1, len(population_individuals[0].objectives))))  # TODO fitnesses is 0
    # Fill the objectives with all individual from the population and offspring combined.
    all_individuals = [individual for individual in population_individuals]
    all_individuals.extend(offspring)
    for index, individual in enumerate(all_individuals):
        # Negative fitness due to minimum search, TODO can be changed to be a default maximization NSGA.
        objectives[index, :] = [inf if objective is None else -objective for objective in individual.objectives]
    # Perform the NSGA Algorithm
    front_no, max_front = nd_sort(objectives, np.inf)
    crowd_dis = crowding_distance(objectives, front_no)
    sorted_fronts = sort_fronts(objectives, front_no, crowd_dis)
    # Select the new individuals based on the population size, since they are sorted we can index them directly.
    new_individuals = [all_individuals[index] for index in sorted_fronts[:population_size]]
    if debug:
        discarded_individuals = [all_individuals[index] for index in sorted_fronts[population_size:]]
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
        plt.scatter(individual.objectives[0], individual.objectives[1], s=5, color='black')
    for individual in discarded_population:
        plt.scatter(individual.objectives[0], individual.objectives[1], s=5, color='white')


# adapted from https://www.programmersought.com/article/6084850621/
def nd_sort(objectives: np.ndarray, max_range: float) -> (List[int], int):
    """
    Non-dominated Sorting algorithm
    :param objectives: objective matrix
    :param max_range:
    :return: (front numbers, biggest front number)
    """
    number_of_individuals, number_of_objectives = objectives.shape[0], objectives.shape[1]
    sorted_matrix = np.lexsort(objectives[:, ::-1].T)  # loc1 is the position of the new matrix element in the old matrix, sorted from the first column in order
    sorted_objectives = objectives[sorted_matrix]
    inverse_sorted_indexes = sorted_matrix.argsort()  # loc2 is the position of the old matrix element in the new matrix
    front_no = np.ones(number_of_individuals) * np.inf  # Initialize all levels to np.inf
    max_front_no = 0  # 0
    while np.sum(front_no < np.inf) < min(max_range, number_of_individuals):  # The number of individuals assigned to the rank does not exceed the number of individuals to be sorted
        max_front_no = max_front_no + 1
        for i in range(number_of_individuals):
            if front_no[i] == np.inf:
                dominated = False
                for j in range(i):
                    if front_no[j] == max_front_no:
                        m = 0
                        flag = 0
                        while m < number_of_objectives and sorted_objectives[i, m] >= sorted_objectives[j, m]:
                            if sorted_objectives[i, m] == sorted_objectives[j, m]:  # does not constitute a dominant relationship
                                flag = flag + 1
                            m = m + 1
                        if m >= number_of_objectives and flag < number_of_objectives:
                            dominated = True
                            break
                if not dominated:
                    front_no[i] = max_front_no
    front_no = front_no[inverse_sorted_indexes]
    return front_no, max_front_no


# adapted from https://github.com/ChengHust/NSGA-II/blob/master/crowding_distance.py
def crowding_distance(objectives, front_number):
    """
    The crowding distance of each Pareto front
    :param objectives: objective vectors
    :param front_number: front numbers
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
    front_dict = dict()  # dictionary indexed by front number inserting objective with crowd distance as tuple
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
