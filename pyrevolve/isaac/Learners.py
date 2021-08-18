import time
import numpy as np
from thirdparty.reversible_de.algorithms.recombination import DifferentialRecombination
from thirdparty.reversible_de.algorithms.selections import SelectBest


class DifferentialEvolution:
    def __init__(self, x0, num_env, de_type='de', bounds=(0, 1), params=None, output_dir="./results"):
        self.population_size = x0.shape[0]
        self.num_env = num_env
        self.gen = 0
        self.x_new = x0
        self.x = x0[0:0]
        self.f = x0[0:0]

        self.f_best_so_far = []
        self.x_best_so_far = []

        self.differential = DifferentialRecombination(type=de_type, bounds=bounds, params=params)
        self.selection = SelectBest()

        self.directory_name = output_dir
        self.fitnesses = []
        self.genomes = []

    def add_eval(self, fitness):
        current_genome, self.x_new = self.x_new[:1], self.x_new[1:]
        self.x = np.vstack((self.x, current_genome))
        self.f = np.append(self.f, fitness)

    def get_new_weights(self):
        if self.x_new.shape[0] == 0:
            self.new_pop()
            if type(self.x_new) == tuple:
                self.x_new = np.concatenate(self.x_new, 0)
        return self.x_new[:self.num_env]

    def new_pop(self):
        x, f = self.selection.select(self.x, self.f, population_size=self.population_size)

        f_min = np.min(f)
        if self.f_best_so_far == [] or f_min < self.f_best_so_far[-1]:
            self.f_best_so_far.append(f_min)

            ind_min = np.argmin(f)

            self.x_best_so_far.append(x[[ind_min]])
        else:
            self.x_best_so_far.append(self.x_best_so_far[-1])
            self.f_best_so_far.append(self.f_best_so_far[-1])

        self.x_new, _ = self.differential.recombination(x)
        self.x = x
        self.f = f

        self.genomes.append(self.x)
        self.fitnesses.append(self.f)

        self.gen += 1
        # print(f"New population, gen: {self.gen} \t | \t {time.clock()}")

    def save_results(self):
        np.save(self.directory_name + '/' + 'fitnesses', np.array(self.fitnesses))
        np.save(self.directory_name + '/' + 'genomes', np.array(self.genomes))

        np.save(self.directory_name + '/' + 'f_best', np.array(self.f_best_so_far))
        np.save(self.directory_name + '/' + 'x_best', np.array(self.x_best_so_far))

    def save_checkpoint(self):
        self.save_results()
        np.save(self.directory_name + '/' + 'last_x_new', np.array(self.x_new))
        np.save(self.directory_name + '/' + 'last_x', np.array(self.x))
        np.save(self.directory_name + '/' + 'last_f', np.array(self.f))
