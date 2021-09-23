from typing import List
from .config import Config
from pyrevolve.genotype.genotype import Genotype


def crossover(parents: List[Genotype], config: Config) -> Genotype:
    return parents[0]
