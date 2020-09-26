import os

import asyncio

from pyrevolve import parser
from pyrevolve.evolution.population import PopulationConfig, Population
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding import PlasticodingConfig
from pyrevolve.revolve_bot.revolve_module import CoreModule

#path = "battery_experiment/1//data_fullevolution/genotypes/"
root_path = "output_fix_moves"

settings = parser.parse_args()
settings.manager = "test_generations"
experiment_management = ExperimentManagement(settings)
experiment_management._data_folder = "output_individuals"

genotype_conf = PlasticodingConfig(
    max_structural_modules=100,
    allow_vertical_brick=False,
    use_rotation_commands=False,
    use_movement_stack=False

)

mutation_conf = MutationConfig(
    mutation_prob=0.8,
    genotype_conf=genotype_conf,
)

crossover_conf = CrossoverConfig(
    crossover_prob=0.8,
)
# experiment params #

population_conf = PopulationConfig(
    population_size=100,
    genotype_constructor=random_initialization,
    genotype_conf=genotype_conf,
    fitness_function=None,
    mutation_operator=None,
    mutation_conf=mutation_conf,
    crossover_operator=None,
    crossover_conf=crossover_conf,
    selection=None,
    parent_selection=None,
    population_management=None,
    population_management_selector=None,
    evaluation_time=None,
    offspring_size=None,
    experiment_name="test_generation",
    experiment_management=experiment_management,
)

population = Population(population_conf, None)

def _create_path(path):
    print(path)
    if not os.path.exists(path):
        os.mkdir(path)


def generate():
    _create_path(root_path)
    _create_path(os.path.join(root_path, "descriptors"))
    _create_path(os.path.join(root_path, "fitness"))
    _create_path(os.path.join(root_path, "genotypes"))
    _create_path(os.path.join(root_path, "phenotypes"))
    _create_path(os.path.join(root_path, "images"))

    for i in range(population.conf.population_size):
        individual = population._new_individual(population.conf.genotype_constructor(population.conf.genotype_conf, population.next_robot_id))
        population.individuals.append(individual)
        population.next_robot_id += 1
        experiment_management.export_behavior_measures(i+1, None)

    for individual in population.individuals:
        individual.export(root_path)
        individual.phenotype.render_body(
            os.path.join(root_path, "images", f'body_{individual.phenotype.id}.png'))
        individual.phenotype.render_brain(
            os.path.join(root_path, "images", f'brain_{individual.phenotype.id}.png'))


async def analyze():
    if len(population.individuals) == 0:
        print("recover")
        for i in range(population_conf.population_size):
            try:
                population.individuals.append(await population.load_individual(i+1))
            except FileNotFoundError:
                pass

    core_limbs = []
    for individual in population.individuals:
        core_limbs.append(4 - individual.phenotype._body.children.count(None))

    for i in range(4):
        print(core_limbs.count(i+1) / len(core_limbs))

    print([i for i, x in enumerate(core_limbs) if x == 3], [i for i, x in enumerate(core_limbs) if x == 4])

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # Blocking call which returns when the display_date() coroutine is done
    generate()
    loop.run_until_complete(analyze())
    loop.close()
