import xml.etree.ElementTree
from typing import Tuple

from .cpg import BrainCPG


# Extends BrainCPG by including a Genome
class BrainCPGTarget(BrainCPG):
    TYPE = "cpg-target"

    # unit vector, target direction
    target: Tuple[float, float, float] = (0, 0, 0)

    @staticmethod
    def from_yaml(yaml_object):
        brain = BrainCPGTarget()
        for my_type in ["controller", "learner"]:  # , "meta"]:
            try:
                my_object = yaml_object[my_type]
                for key, value in my_object.items():
                    try:
                        setattr(brain, key, value)
                    except:
                        print("Couldn't set {}, {}", format(key, value))
            except:
                print("Didn't load {} parameters".format(my_type))
        return brain

    def to_yaml(self):
        yaml = super().to_yaml()
        yaml["controller"]["target"] = self.target

    def controller_sdf(self):
        sdf = super().controller_sdf()
        sdf.set("target", ";".join(str(x) for x in self.target))
        return sdf
