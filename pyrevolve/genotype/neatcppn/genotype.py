from __future__ import annotations

import multineat
from pyrevolve.genotype import Genotype
from pyrevolve.genotype.neatcppn.config import NeatcppnGenotypeConfig
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.brain import BrainCPPNCPG


class NeatcppnGenotype(Genotype):
    _id: int
    _config: NeatcppnGenotypeConfig
    _multineat_genome: multineat.Genome

    def __init__(self, config: NeatcppnGenotypeConfig, robot_id: int):
        self._id = robot_id

        self._multineat_genome = multineat.Genome(
            0,  # ID
            config.brain_n_inputs,
            0,  # n_hidden
            config.brain_n_outputs,
            False,  # FS_NEAT
            multineat.ActivationFunction.TANH,  # output activation type
            multineat.ActivationFunction.TANH,  # hidden activation type
            0,  # seed_type
            config.brain_multineat_params,
            0,  # number of hidden layers
        )

    def clone(self) -> NeatcppnGenotype:
        new = NeatcppnGenotype.__new___(NeatcppnGenotype)
        new._id = self._id
        new._multineat_genome = multineat.Genome(self._brain_genome)

    def develop(self) -> RevolveBot:
        return self._config._develop_function(
            self._config._develop_userdata, self._id, self._multineat_genome
        )
        """
        brain = BrainCPPNCPG(self._neat_genome) # TODO convert CPPN to CPG weights and use CPG brain class
        for key, value in self._config.items():
            setattr(brain, key, value)

        phenotype = RevolveBot(self._id)
        phenotype._body = None # TODO
        phenotype._brain = brain

        return phenotype
        """
