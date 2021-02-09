import pickle
from typing import Optional

from pyrevolve.angle import Tree
from pyrevolve.genotype import Genotype
from pyrevolve.genotype.direct_tree import DirectTreeConfig
from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from pyrevolve.genotype.direct_tree.revolve_bot_adapter import RevolveBotAdapter
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.brain import BrainNN
from pyrevolve.tol.spec import get_tree_generator


class DirectTreeGenomeConfig(object):
    pass


class DirectTreeGenotype(Genotype):

    def __init__(self, conf: DirectTreeConfig, robot_id: Optional[int]):
        """
        :param conf: configurations for l-system
        :param robot_id: unique id of the robot
        :type conf: PlasticodingConfig
        """
        self.conf: DirectTreeConfig = conf
        assert robot_id is None or str(robot_id).isdigit()
        self.id: int = int(robot_id) if robot_id is not None else -1

        self.representation: Tree = None
        self.generator: RobogenTreeGenerator = None

        # Auxiliary variables
        self.valid: bool = False
        self.phenotype: Optional[RevolveBot] = None

    def clone(self):
        # Cannot use deep clone for this genome, because it is bugged sometimes
        _id = self.id if self.id >= 0 else None
        other = DirectTreeGenotype(self.conf, _id)
        other.valid = self.valid
        other.representation = self.representation
        other.generator = self.generator
        other.phenotype = self.phenotype
        return other

    def load_genotype(self, genotype_filename: str) -> None:
        genotype_filename = genotype_filename.replace(".txt", ".pickle")
        with open(genotype_filename, 'rb') as handle:
            self.representation.root = pickle.load(handle)

    def export_genotype(self, genotype_filename: str) -> None:
        genotype_filename = genotype_filename.replace(".txt", ".pickle")
        with open(genotype_filename, 'wb') as handle:
            pickle.dump(self.representation.root, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def check_validity(self) -> None:
        self.valid = self.phenotype._morphological_measurements.measurements_to_dict()['hinge_count'] > 0

    def develop(self) -> RevolveBot:
        # TODO develop from self.genotype into self.phenotype
        if self.phenotype is None:
            self.phenotype = RevolveBot(self.id)
            self.phenotype._body = RevolveBotAdapter().body_from_tree(self.representation)
            self.phenotype._brain = BrainNN()
            # TODO generate brain from oscillators
        return self.phenotype
