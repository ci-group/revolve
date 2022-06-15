from __future__ import annotations

from typing import Optional, TextIO, AnyStr, List

from pyrevolve.genotype import Genotype
from pyrevolve.genotype.direct_tree import direct_tree_random_generator
from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeGenotypeConfig
from pyrevolve.genotype.direct_tree.direct_tree_utils import duplicate_subtree
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.brain import BrainNN, brain_nn, BrainCPPNCPG
from pyrevolve.revolve_bot.revolve_module import ActiveHingeModule
from pyrevolve.revolve_bot.revolve_module import CoreModule


class DirectTreeGenotype(Genotype):

    def __init__(self, conf: DirectTreeGenotypeConfig, robot_id: Optional[int], random_init=True):
        """
        :param conf: configurations for l-system
        :param robot_id: unique id of the robot
        :type conf: PlasticodingConfig
        """
        self.conf: DirectTreeGenotypeConfig = conf
        assert robot_id is None or str(robot_id).isdigit()
        self.id: int = int(robot_id) if robot_id is not None else -1

        if random_init:
            assert robot_id is not None
            assert conf is not None
            self.representation: CoreModule = CoreModule()
            self.random_initialization()
        else:
            self.representation = None

        # Auxiliary variables
        self.valid: bool = False

        self.phenotype: Optional[RevolveBot] = None

    def clone(self):
        # Cannot use deep clone for this genome, because it is bugged sometimes
        _id = self.id if self.id >= 0 else None

        other = DirectTreeGenotype(self.conf, _id, random_init=False)
        other.valid = self.valid
        other.representation = duplicate_subtree(self.representation)

        other.phenotype = None
        return other

    def load_genotype(self, genotype_filename: AnyStr) -> None:
        revolvebot: RevolveBot = RevolveBot()
        revolvebot.load_file(genotype_filename, conf_type='yaml')
        self._load_genotype_from_revolvebot(revolvebot)

    def _load_genotype_from_lines(self, genotype_lines: List[AnyStr], only_body=False) -> None:
        revolvebot: RevolveBot = RevolveBot()
        revolvebot.load('\n'.join(genotype_lines), conf_type='yaml')
        if only_body:
            self._load_genotype_only_body(revolvebot)
        else:
            self._load_genotype_from_revolvebot(revolvebot)

    def _load_genotype_only_body(self, revolvebot: RevolveBot) -> None:
        self.id = revolvebot.id
        self.representation = revolvebot._body        

    def _load_genotype_only_brain(self, revolvebot: RevolveBot) -> None:
        # load brain params into the modules
        brain = revolvebot._brain
        
        assert isinstance(brain, BrainCPPNCPG)

        module_map = {}
        for module in revolvebot.iter_all_elements():
            assert module.id not in module_map
            module_map[module.id] = module

        for node_id, oscillator in brain.params.items():
            node = brain.nodes[node_id]
            module_map[node.part_id].oscillator_amplitude = oscillator.amplitude
            module_map[node.part_id].oscillator_period = oscillator.period
            module_map[node.part_id].oscillator_phase = oscillator.phase_offset

        for module in revolvebot.iter_all_elements():
            assert module_map[module.id] == module

    def _load_genotype_from_revolvebot(self, revolvebot: RevolveBot) -> None:
        self._load_genotype_only_body(revolvebot=revolvebot)
        self._load_genotype_only_brain(revolvebot=revolvebot)

    def export_genotype(self, filepath: str) -> None:
        self.develop()
        self.phenotype.save_file(filepath, conf_type='yaml')

    def _export_genotype_open_file(self, open_file: TextIO, onlyBody:bool = False) -> None:
        self.develop()
        serialized_yaml = self.phenotype.to_yaml(onlyBody=onlyBody)
        open_file.write(serialized_yaml)

    def develop(self) -> RevolveBot:
        if self.phenotype is None:
            self.phenotype: RevolveBot = RevolveBot(self.id)
            self.phenotype._body = self.representation
            self.phenotype._brain = self._develop_brain(self.representation)
        return self.phenotype

    def _develop_brain(self, core: CoreModule):
        brain = BrainNN()

        for module in self.phenotype.iter_all_elements():
            if isinstance(module, ActiveHingeModule):
                node = brain_nn.Node()
                node.id = f'node_{module.id}'
                node.part_id = module.id

                node.layer = 'output'
                node.type = 'Oscillator'

                params = brain_nn.Params()
                params.period = module.oscillator_period
                params.phase_offset = module.oscillator_phase
                params.amplitude = module.oscillator_amplitude
                node.params = params

                brain.params[node.id] = params
                brain.nodes[node.id] = node

        # add imu sensor stuff or the brain fail to load
        for p in range(1, 7):
            _id = 'IMU_' + str(p)
            node = brain_nn.Node()
            node.layer = 'input'
            node.type = 'Input'
            node.part_id = core.id
            node.id = _id
            brain.nodes[_id] = node

        return brain

    def random_initialization(self):
        self.representation = direct_tree_random_generator.generate_tree(self.representation,
                                                                         max_parts=self.conf.max_parts,
                                                                         n_parts_mu=self.conf.init.n_parts_mu,
                                                                         n_parts_sigma=self.conf.init.n_parts_sigma,
                                                                         config=self.conf)
        return self

    def mutate(self):
        from pyrevolve.genotype.direct_tree.direct_tree_mutation import mutate
        return mutate(self, self.conf, in_place=False)

    def crossover(self, other: DirectTreeGenotype, new_id: int):
        from pyrevolve.genotype.direct_tree.direct_tree_crossover import crossover
        return crossover(self, other, self.conf, new_id)
