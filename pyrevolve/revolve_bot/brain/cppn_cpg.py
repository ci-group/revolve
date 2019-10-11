from .cpg import BrainCPG
import xml.etree.ElementTree


# Extends BrainCPG by including a Genome
class BrainCPPNCPG(BrainCPG):
    TYPE = 'cppn-cpg'

    def __init__(self):
        super().__init__()
        self.genome = None

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {
            'type': 'cppn-cpg',
            'abs_output_bound': str(self.abs_output_bound),
            'reset_robot_position': str(self.reset_robot_position),
            'reset_neuron_state_bool': str(self.reset_neuron_state_bool),
            'reset_neuron_random': str(self.reset_neuron_random),
            'load_brain': str(self.load_brain),
            'use_frame_of_reference': str(self.use_frame_of_reference),
            'run_analytics': str(self.run_analytics),
            'init_neuron_state': str(self.init_neuron_state),
            'output_directory': str(self.output_directory),
            'verbose': str(self.verbose),
            'range_lb': str(self.range_lb),
            'range_ub': str(self.range_ub),
            'signal_factor_all': str(self.signal_factor_all),
            'signal_factor_mid': str(self.signal_factor_mid),
            'signal_factor_left_right': str(self.signal_factor_left_right),
            'startup_time': str(self.startup_time),
            'weight_genome': self.genome_sdf(),
        })

    def genome_sdf(self):
        # TODO Build a sdf that contains the genome of the brain
        return xml.etree.ElementTree.Element('rv:genome', {
            'none':'none'
        })
