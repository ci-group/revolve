from dataclasses import dataclass

from ..direct_tree.direct_tree_config import DirectTreeGenotypeConfig
from ..plasticoding.mutation.mutation import MutationConfig


@dataclass
class Config:
    directtree_config: DirectTreeGenotypeConfig
    mutation_prob: float
    crossover_prob: float
