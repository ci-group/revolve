import asyncio
import os
import sys
from thirdparty.pycma import cma
import time
import threading
from pyrevolve.gazebo.manage import WorldManager as World
from pyrevolve.SDF.math import Vector3


class Learning:
    def __init__(self, individual, simulator_connection, population_conf, max_func_evals=100):
        """
        :param individual: individual to perform learning on brain
        """
        self.individual = individual
        self.robot_id = None
        self.vector_values = None
        self.param_references = None
        self.simulator_connection = simulator_connection
        self.population_conf = population_conf
        self.max_func_evals = max_func_evals
        self.learn_counter = 0
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
        return best[0], best[1]

    async def cma_es_evaluate_vector(self, vector):
        """
        :param vector: list of vector values to evaluate in individual
        :return: fitness of vector
        """
        if self.param_references is None:
            return

        self.vector_values = vector

        if self.robot_id is None:
            self.robot_id = self.individual.phenotype.id

        # set unique robot id
        self.individual.phenotype._id = f'{self.robot_id}_{self.learn_counter}'

        # set vector in brain to collect fitness of robot
        self.devectorize_brain(vector)

        # parameter values must be in range <-10, 10>
        self.ensure_bounds_parameters()

        #self.individual.phenotype.save_file(f'/home/vm/Downloads/robots_sdf/{self.individual.phenotype._id}.sdf', 'sdf')

        future = self.simulator_connection.test_robot(self.individual, self.population_conf)
        self.individual.fitness = await future

        self.vectors_fitnessess[self.individual.phenotype._id] = [self.individual.fitness, vector]

        self.learn_counter += 1

        # return negative fitness, as cma lib makes use of base fitness function
        return -self.individual.fitness

    async def vector_cma_es(self):
        """
        Covariance matrix adaptation evolution strategy
        :return: best vector result
        """
        # cma evolution strategy with sigma set to 0.5
        cma_strategy = cma.CMAEvolutionStrategy(self.vector_values, 0.5)
        await cma_strategy.optimize(self.cma_es_evaluate_vector, maxfun=self.max_func_evals)

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
        await self.cma_es_evaluate_vector(self.vector_values)

        # algorithm does not work for empty vectors
        if len(self.vector_values) > 0:
            best_vector = await self.vector_cma_es()
            self.devectorize_brain(best_vector)

        # set correct fitness for best vector in individual
        await self.cma_es_evaluate_vector(best_vector)

        return self.individual
