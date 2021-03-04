import re

import numpy as np

from pyrevolve.genotype import Genotype
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import BrainType
from pyrevolve.genotype.plasticoding import Plasticoding
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.revolve_bot.brain import BrainCPG


class CPGBrainGenomeConfig:
    def __init__(self, brain_type: BrainType = BrainType.CPG, random_seed=None):
        self._brain_type = brain_type
        # CPG parameters

    @property
    def brain_type(self):
        return self._brain_type

    @brain_type.setter
    def brain_type(self, brain_type: BrainType):
        self._brain_type = brain_type


class CPGBrainGenome(Genotype):
    def __init__(self):  # Change

        # self.id = int(robot_id)
        self._brain_type = BrainType.CPG

        self._brain_genome: BrainCPG = None

    def load_genotype(self, file_path: str):
        with open(file_path) as f:
            lines = f.readlines()
            self._load_genotype_from(lines[0])

    def _load_genotype_from(self, text):
        text = text.strip()
        for element in text:
            pass
            # TODO self.weights.append(float(element))

    def export_genotype(self, file_path: str):
        with open(file_path, 'w+') as file:
            self._export_genotype_open_file(file)

    def _export_genotype_open_file(self, file):
        text = ""
        #for element in self._:
        #    text += str(element) + " "
        file.write(text + '\n')

    # override
    def clone(self):
        clone = CPGBrainGenome()
        clone._brain_type = self._brain_type  # the conf must not be deep copied
        clone._brain_genome = self._brain_genome
        return clone

    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, value: int):
        self._id = value

    def develop(self, revolve_bot):
        if self._brain_type is BrainType.CPG:
            # basically, HyperNEAT
            self.brain = BrainCPG(revolve_bot)

            self.brain.reset_neuron_random = False
            self.brain.use_frame_of_reference = False
            self.brain.init_neuron_state = 0.707
            self.brain.range_ub = 1.0
            self.brain.signal_factor_all = 4.0
            self.brain.signal_factor_mid = 2.5
            self.brain.signal_factor_left_right = 2.5
            self.brain.abs_output_bound = 1.0
            self.brain.weights = []
        else:
            raise NotImplementedError(f"{self._brain_type} brain not implemented yet")

        return self.brain
