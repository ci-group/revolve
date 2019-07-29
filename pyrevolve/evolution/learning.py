import time
import copy
import asyncio
import numpy as np
from thirdparty.pycma import cma

class Learning:
    def __init__(self, individual, generation, simulator_connection, population_conf, population=None):
        """
        :param individual: individual to perform learning on brain
        """
        #DELETE#####################
        self.times_over_10s = 0
        ############################
        self.individual = individual
        self.robot_id = None
        self.generation = generation
        self.vector_values = None
        self.param_references = None
        self.simulator_connection = simulator_connection
        self.population_conf = population_conf
        self.population = population
        self.original = None
        self.best = None
        self.learn_counter = 0
        self.started_evals = False
        self.vectors_fitnessess = {}

    def vectorize_brain(self):
        """
        Cast brain parameters into vector of values
        """
        self.param_references = {}
        self.vector_values = []
        brain = self.individual.phenotype._brain

        if brain is None:
            return

        # vectorize parameter values
        for node in brain.nodes:
            if node in brain.params:
                self.param_references[f'{node}_period'] = len(self.vector_values)
                self.vector_values.append(brain.params[node].period)
                self.param_references[f'{node}_offset'] = len(self.vector_values)
                self.vector_values.append(brain.params[node].phase_offset)
                self.param_references[f'{node}_amplitude'] = len(self.vector_values)
                self.vector_values.append(brain.params[node].amplitude)

    def devectorize_brain(self, vector):
        """
        Cast vectorized values back into original brain parameters
        """
        brain = self.individual.phenotype._brain

        if brain is None or self.vector_values is None or self.param_references is None:
            return

        self.vector_values = vector

        # cast vector values back into brain
        for node in brain.nodes:
            if node in brain.params:
                brain.params[node].period = float(self.vector_values[self.param_references[f'{node}_period']])
                brain.params[node].phase_offset = float(self.vector_values[self.param_references[f'{node}_offset']])
                brain.params[node].amplitude = float(self.vector_values[self.param_references[f'{node}_amplitude']])

        self.individual.phenotype._brain = brain

    def ensure_bounds_parameters(self):
        """
        Ensure upper/lower bounds of brain parameters: <-10, +10>
        """
        vector_bounds_ensured = []

        self.vectorize_brain()

        for i in range(len(self.vector_values)):
            val = self.vector_values[i]
            val = 10 if val > 10 else val
            val = -10 if val < -10 else val
            vector_bounds_ensured.append(val)

        self.devectorize_brain(vector_bounds_ensured)

    def best_vector_fitness(self):
        """
        Get vector with best aqcuired fitness
        :return: fitness, vector
        """
        best_vector_key = max(self.vectors_fitnessess, key=self.vectors_fitnessess.get)
        best = self.vectors_fitnessess[best_vector_key]
        self.best = best
        return best[0], best[1]

    async def cma_es_evaluate_multiple_vectors(self, vectors):
        """
        :param vector: list of list of vector values to evaluate
        :return: list of fitnesses of vectors
        """
        individuals = []
        fitness_vals = []

        vectors = [vector.tolist() if isinstance(vector, np.ndarray) else vector for vector in vectors]

        for vector in vectors:
            self.vector_values = vector

            if self.robot_id is None and self.started_evals is False:
                self.robot_id = self.individual.phenotype.id

            # set unique robot id
            self.individual.phenotype._id = f'{self.robot_id}_gen_{self.generation}_li_{self.learn_counter}'

            # set vector in brain to collect fitness of robot
            self.devectorize_brain(vector)

            # parameter values must be in range <-10, 10>
            self.ensure_bounds_parameters()

            new_individual = self.individual
            individuals.append(copy.deepcopy(new_individual))

            self.learn_counter += 1
            self.started_evals = True


        await self.population.evaluate(individuals, self.generation, learn_eval=True)

        for individual in individuals:
            fitness_vals.append(-individual.fitness)

        for individual, vector in zip(individuals, vectors):
            self.population_conf.experiment_management.export_cma_learning_fitness(self.robot_id, self.generation, vector, individual.fitness)
            self.vectors_fitnessess[individual.phenotype._id] = [individual.fitness, vector]

        return fitness_vals

    async def cma_es_evaluate_vector(self, vector, np_array=True):
        """
        :param vector: list of vector values to evaluate in individual
        :return: fitness of vector
        """
        if self.param_references is None:
            return
        
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()

        self.vector_values = vector

        if self.robot_id is None and self.started_evals is False:
            self.robot_id = self.individual.phenotype.id

        # set unique robot id
        self.individual.phenotype._id = f'{self.robot_id}_gen_{self.generation}_li_{self.learn_counter}'

        # set vector in brain to collect fitness of robot
        self.devectorize_brain(vector)

        # parameter values must be in range <-10, 10>
        self.ensure_bounds_parameters()

        # put robot in simulator and retrieve fitness
        future = self.simulator_connection.test_robot(self.individual, self.population_conf)
        self.individual.fitness = await future

        # store fitness to be restored in case of crash
        self.population_conf.experiment_management.export_cma_learning_fitness(self.robot_id, self.generation, vector, self.individual.fitness)

        self.vectors_fitnessess[self.individual.phenotype._id] = [self.individual.fitness, vector]

        self.learn_counter += 1
        self.started_evals = True

        # return negative fitness, as cma lib makes use of base fitness function
        return -self.individual.fitness

    async def vector_cma_es(self):
        """
        Covariance matrix adaptation evolution strategy
        :return: best vector result
        """
        recovered_learning = False
        recovered_learning_previous_gens = False
        
        # check if learning has crashed in previous run and get fitness values
        if self.population_conf.experiment_management.cma_learning_is_recoverable(self.robot_id, self.generation):
            recovered_learning = self.population_conf.experiment_management.recover_cma_learning_fitnesses(self.robot_id, self.generation)
            recovered_learning = False if len(recovered_learning[0]) == 1 else recovered_learning
        
        if recovered_learning:
            i = 1
            for vector, fitness in zip(recovered_learning[0], recovered_learning[1]):
                self.vectors_fitnessess[f'recovered_{i}'] = [fitness, vector]
                i+=1
        
        # recover learning from previous generations
        if self.population_conf.learn_lamarckian:
            if self.population_conf.experiment_management.cma_learning_is_recoverable(self.robot_id, self.generation-1):
                recovered_learning_previous_gens = self.population_conf.experiment_management.recover_previous_gens(self.robot_id, self.generation)

        # cma evolution strategy with sigma set to 0.5 (initial std)
        cma_strategy = cma.CMAEvolutionStrategy(self.vector_values, 0.5)
        await cma_strategy.optimize(self.cma_es_evaluate_multiple_vectors, maxfun=self.population_conf.max_learn_evals, recovery_vec_fit=recovered_learning, recovery_previous_gens=recovered_learning_previous_gens)

        # return best vector
        best_vector = cma_strategy.result.xbest
        return best_vector

    async def learn_brain_through_cma_es(self):
        """
        Learn brain parameters by optimization through CMA-ES
        :return: individual with learned brain parameters
        """
        if self.individual.phenotype._brain is None:
            return

        # turn brain into vector for cma
        self.vectorize_brain()

        # set original fitness of robot as first index of list fitnesses_aqcuired
        original_fitness = await self.cma_es_evaluate_vector(self.vector_values, False)
        self.original = [original_fitness, self.vector_values]

        # algorithm does not work for empty vectors
        if len(self.vector_values) > 0:
            best_vector = await self.vector_cma_es()
            self.devectorize_brain(best_vector)
        else:
            self.individual.phenotype._id = self.robot_id
            return self.individual

        # set correct fitness for best vector in individual
        await self.cma_es_evaluate_vector(self.vector_values, False)

        self.best_vector_fitness()

        self.individual.phenotype._id = self.robot_id

        return self.individual
