import sys
import xml.etree.ElementTree
import multineat

from .cpg import BrainCPG


# Extends BrainCPG by including a Genome
class BrainCPPNCPG(BrainCPG):
    TYPE = "cppn-cpg"

    def __init__(self, neat_genome):
        super().__init__()
        self.genome = neat_genome
        self.weights = None

    def to_yaml(self):
        obj = super().to_yaml()
        obj["controller"]["cppn"] = self.genome.Serialize()
        return obj

    @staticmethod
    def from_yaml(yaml_object):
        cppn_genome = multineat.Genome()
        cppn_genome.Deserialize(
            yaml_object["controller"]["cppn"].replace("inf", str(sys.float_info.max))
        )
        del yaml_object["controller"]["cppn"]

        BCPG = BrainCPPNCPG(cppn_genome)
        for my_type in ["controller", "learner"]:
            try:
                my_object = yaml_object[my_type]
                for key, value in my_object.items():
                    try:
                        setattr(BCPG, key, value)
                    except:
                        print("Couldn't set {}, {}", format(key, value))
            except:
                print("Didn't load {} parameters".format(my_type))

        return BCPG

    def controller_sdf(self):
        controller = xml.etree.ElementTree.Element(
            "rv:controller",
            {
                "type": "cppn-cpg",
                "abs_output_bound": str(self.abs_output_bound),
                "reset_robot_position": str(self.reset_robot_position),
                "reset_neuron_state_bool": str(self.reset_neuron_state_bool),
                "reset_neuron_random": str(self.reset_neuron_random),
                "load_brain": str(self.load_brain),
                "use_frame_of_reference": str(self.use_frame_of_reference),
                "run_analytics": str(self.run_analytics),
                "init_neuron_state": str(self.init_neuron_state),
                "output_directory": str(self.output_directory),
                "verbose": str(self.verbose),
                "range_lb": str(self.range_lb),
                "range_ub": str(self.range_ub),
                "signal_factor_all": str(self.signal_factor_all),
                "signal_factor_mid": str(self.signal_factor_mid),
                "signal_factor_left_right": str(self.signal_factor_left_right),
                "startup_time": str(self.startup_time),
            },
        )
        controller.append(self.genome_sdf())
        return controller

    def genome_sdf(self):
        assert self.genome is not None
        serialized_genome = self.genome.Serialize()

        element = xml.etree.ElementTree.Element("rv:genome", {"type": "CPPN"})
        element.text = serialized_genome

        return element
