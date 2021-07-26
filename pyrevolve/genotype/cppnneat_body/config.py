from dataclasses import dataclass

import multineat


@dataclass
class CppnneatBodyConfig:
    innov_db: multineat.InnovationDatabase
    rng: multineat.RNG
