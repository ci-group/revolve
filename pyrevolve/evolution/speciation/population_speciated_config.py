
from ..population import PopulationConfig


class PopulationSpeciatedConfig(PopulationConfig):
    def __init__(self,
                 population_size: int,
                 genotype_constructor,
                 genotype_conf,
                 fitness_function,
                 mutation_operator,
                 mutation_conf,
                 crossover_operator,
                 crossover_conf,
                 selection,
                 parent_selection,
                 population_management,
                 population_management_selector,
                 evaluation_time,
                 experiment_name,
                 experiment_management,
                 are_genomes_compatible_fn,
                 young_age_threshold: int,
                 young_age_fitness_boost: float,
                 old_age_threshold: int,
                 old_age_fitness_penalty: float,
                 offspring_size=None):
        super().__init__(population_size,
                         genotype_constructor,
                         genotype_conf,
                         fitness_function,
                         mutation_operator,
                         mutation_conf,
                         crossover_operator,
                         crossover_conf,
                         selection,
                         parent_selection,
                         population_management,
                         population_management_selector,
                         evaluation_time,
                         experiment_name,
                         experiment_management,
                         offspring_size)
        self.are_genomes_compatible = are_genomes_compatible_fn
        self.young_age_threshold = young_age_threshold
        self.young_age_fitness_boost = young_age_fitness_boost
        self.old_age_threshold = old_age_threshold
        self.old_age_fitness_penalty = old_age_fitness_penalty

