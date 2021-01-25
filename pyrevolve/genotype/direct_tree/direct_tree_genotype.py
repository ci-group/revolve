from typing import Optional, List

from pyrevolve.angle import Tree
from pyrevolve.angle.robogen import Config
from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.tol.spec import get_tree_generator


class DirectTreeGenomeConfig(object):
    pass


class DirectTreeGenome(object):

    def __init__(self, conf: Config, robot_id: Optional[int]):
        """
        :param conf: configurations for l-system
        :param robot_id: unique id of the robot
        :type conf: PlasticodingConfig
        """
        self.conf: Config = conf
        assert robot_id is None or str(robot_id).isdigit()
        self.id: int = int(robot_id) if robot_id is not None else -1

        self.root: Tree = None

        # Auxiliary variables
        self.valid: bool = False
        self.phenotype: Optional[RevolveBot] = None

    def clone(self):
        # Cannot use deep clone for this genome, because it is bugged sometimes
        _id = self.id if self.id >= 0 else None
        other = DirectTreeGenome(self.conf, _id)
        other.valid = self.valid
        other.root = self.root
        other.phenotype = self.phenotype
        return other

    def load_genotype(self, genotype_filename: str) -> None:
        with open(genotype_filename) as f:
            lines = f.readlines()
            self._load_genotype_from(lines)

    def _load_genotype_from(self, lines: List[str]) -> None:
        for line in lines:
            line_array = line.split(' ')
            #TODO

    def export_genotype(self, filepath: str) -> None:
        with open(filepath, 'w+') as file:
            self._export_genotype_open_file(file)

    def _export_genotype_open_file(self, file) -> None:
        #TODO
        pass

    def check_validity(self) -> None:
        if self.phenotype._morphological_measurements.measurements_to_dict()['hinge_count'] > 0:
            self.valid = True

    def develop(self) -> RevolveBot:
        # TODO
        return self.phenotype

    def random_initialization(self):
        generator: RobogenTreeGenerator = get_tree_generator(self.conf)
        self.root = generator.generate_tree()
        return self
