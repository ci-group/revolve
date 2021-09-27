from dataclasses import dataclass
from ..plasticoding import PlasticodingConfig



@dataclass
class Config:
    plasticoding_config: PlasticodingConfig
    mutation_prob: float
    crossover_prob: float
