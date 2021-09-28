from dataclasses import dataclass


@dataclass
class Config:
    mutation_prob: float
    crossover_prob: float
