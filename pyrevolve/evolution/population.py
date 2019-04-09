# [(G,P), (G,P), (G,P), (G,P), (G,P)]

from pyrevolve.evolution.individual import Individual
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet
from pyrevolve import parser
from pyrevolve.tol.manage import World
from pyrevolve.SDF.math import Vector3
import time
import asyncio

class PopulationConfig:
	def __init__(self, 
		population_size: int, 
		genotype_constructor, 
		genotype_conf,
		mutation_operator, 
		mutation_conf,
		crossover_operator, 
		selection, 
		parent_selection,
		population_management,
		offspring_size=None):
		"""
		Creates a PopulationConfig object that sets the particular configuration for the population

		:param population_size: size of the population
		:param genotype_constructor: class of the genotype used
		:param genotype_conf: configuration for genotype constructor
		:param mutation_operator: operator to be used in mutation
		:param mutation_conf: configuration for mutation operator
		:param crossover_operator: operator to be used in crossover
		:param selection: selection type
		:param parent_selection: selection type during parent selection
		:param population_management: type of population management ie. steady state or generational
		:param offspring_size (optional): size of offspring (for steady state)
		"""
		self.population_size = population_size
		self.genotype_constructor = genotype_constructor
		self.genotype_conf = genotype_conf
		self.mutation_operator = mutation_operator
		self.mutation_conf = mutation_conf
		self.crossover_operator = crossover_operator
		self.parent_selection = parent_selection
		self.selection = selection
		self.population_management = population_management
		self.offspring_size = offspring_size


class Population:
	def __init__(self, conf):
		"""
		Creates a Population object that initialises the 
		individuals in the population with an empty list 
		and stores the configuration of the system to the 
		conf variable.

		:param conf: configuration of the system
		"""
		self.conf = conf
		self.individuals = []

	def init_pop(self):
		"""
		Populates the population (individuals list) with Individual objects that contains their respective genotype. 
		"""
		for i in range(self.conf.population_size):
			individual = Individual(self.conf.genotype_constructor(self.conf.genotype_conf))
			self.individuals.append(individual)

	async def next_gen(self):
		"""
		Creates next generation of the population through selection, mutation, crossover
		
		:return: new population
		"""
		new_individuals = []

		for _i in range(self.conf.offspring_size):
			# Selection operator (based on fitness)
			# Crossover
			if self.conf.crossover_operator is not None:
				parents = self.conf.parent_selection(self.individuals)
				child = self.conf.crossover_operator(parents)
			else:
				child = self.conf.selection(self.individuals)
			# Mutation operator
			child_genotype = self.conf.mutation_operator(child.genotype, self.conf.mutation_conf)
			# Insert individual in new population
			individual = Individual(child_genotype)
			new_individuals.append(individual)

		# evaluate new individuals
		await self.evaluate(new_individuals)

		# create next population
		new_individuals = self.conf.population_management(self.indidivuals, new_individuals)
		return self.__class__(self.conf, new_individuals)


	async def evaluate(self, new_individuals):
		"""
		Evaluates each individual in the new gen population
		
		"""
		for individual in new_individuals:
			individual.develop()
			await self.evaluate_single_robot(individual)

	async def evaluate_single_robot(self, individual):
		"""
		Evaluate an individual
		
		"""
		# Parse command line / file input arguments
		settings = parser.parse_args()

		# Connect to the simulator and pause
		world = await World.create(settings)
		await world.pause(True)

		await (await world.delete_model(individual.phenotype.id))
		await asyncio.sleep(2.5)

		# Insert the robot in the simulator
		insert_future = await world.insert_robot(individual.phenotype, Vector3(0, 0, 0.25))
		robot_manager = await insert_future

		# Resume simulation
		await world.pause(False)

		# Start a run loop to do some stuff
		duration = time.time() + 30
		while time.time() < duration: # NTS: better way to set time
			# Print robot fitness every second
			fitness = robot_manager.fitness()
			print(f'Robot fitness is {fitness}\n')
			await asyncio.sleep(1.0)

		individual.fitness = fitness