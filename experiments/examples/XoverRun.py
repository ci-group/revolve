
from pyrevolve.evolution import fitness
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management

from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover, generate_child_genotype
from pyrevolve.genotype.plasticoding.initialization import random_gramar_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenome, NeatBrainGenomeConfig, BrainType
from pyrevolve.genotype.lsystem_neat.lsystem_neat_genotype import LSystemCPGHyperNEATGenotypeConfig, LSystemCPGHyperNEATGenotype
from pyrevolve.evolution.individual import Individual
from pyrevolve.genotype.lsystem_neat.crossover import standard_crossover as Lcrossover
from pyrevolve.genotype.lsystem_neat.crossover import CrossoverConfig as LCrossoverConfig
from pyrevolve.genotype.lsystem_neat.mutation import LSystemNeatMutationConf as LMutationConfig
from pyrevolve.genotype.lsystem_neat.mutation import standard_mutation as LMutation
from pyrevolve.evolution.selection import multiple_selection
from pyrevolve.evolution.selection import tournament_selection
from pyrevolve.evolution.selection import _compare_maj_fitness
import random

#Set configuration parts
body_conf = PlasticodingConfig()
brain_conf = NeatBrainGenomeConfig()
lsystem_conf = LSystemCPGHyperNEATGenotypeConfig(body_conf, brain_conf)  #genotype_conf

robot_id = 105
population_size = 4
offspring_size = 2
individuals = []  #Population.individuals

crossover_operator = Lcrossover
crossover_conf = LCrossoverConfig(0.8)

plasticoding_mutation = MutationConfig(
    mutation_prob = 0.8,
    genotype_conf= body_conf,
)

mutation_operator = LMutation
mutation_conf = LMutationConfig(plasticoding_mutation, brain_conf)


#Generate a couple of individuals like in population _new_individual()
class Individual2:
    def __init__(self, genotype, phenotype=None):
        """
        Creates an Individual object with the given genotype and optionally the phenotype.

        :param genotype: genotype of the individual
        :param phenotype (optional): phenotype of the individual
        """
        self.body_genotype = genotype._body_genome
        self.brain_genotype = genotype._brain_genome
        self.phenotype = phenotype
        self.fitness = None
        self.parents = None
        self.failed_eval_attempt_count = 0
    @property
    def id(self):
        _id = None
        if self.phenotype is not None:
            _id = self.phenotype.id
        elif self.body_genotype.id is not None:
            _id = self.body_genotype.id
        return _id

    def __repr__(self):
        return f'Individual_{self.id}({self.fitness})'

for i in range(population_size):
    LGenotype = LSystemCPGHyperNEATGenotype(lsystem_conf, robot_id)  # Genotype structure 1 robot
    LGenotype._body_genome.grammar = random_gramar_initialization(body_conf)  # genotype_constructor
    individual = Individual2(LGenotype)
    individuals.append(individual)
    robot_id += 1

#Do some new individual like in population next_gen()

new_individuals = []
for new_offsprings in range(offspring_size):
    # Selection operator (based on fitness)
    # Crossover
    if crossover_operator is not None:
        parents = multiple_selection(individuals,2,tournament_selection)
        child_genotype = Lcrossover(parents, lsystem_conf, crossover_conf)


    child_genotype._body_genome.id = robot_id
    robot_id += 1

    #mutation
    mutated_child = LMutation(child_genotype, mutation_conf)
















