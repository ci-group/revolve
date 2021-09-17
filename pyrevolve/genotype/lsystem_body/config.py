from dataclasses import dataclass

from ..plasticoding.config import PlasticodingConfig
from ..plasticoding.mutation.mutation import MutationConfig


@dataclass
class Config:
    plasticoding_config: PlasticodingConfig
    mutation_prob: float
    crossover_prob: float
