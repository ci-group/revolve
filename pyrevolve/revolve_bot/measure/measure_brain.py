import numpy as np
import math
# belong to TODO
import fnmatch
from ..brain.brain_nn import BrainNN
from pyrevolve.util.logger import logger


class MeasureBrain:
    def __init__(self, brain: BrainNN, max_param: int):
        """
        Initializing function, for calculating measurements use measure_all
        :param brain: brain to measure, only BrainNN supported
        :param max_param: Range of oscillator parameter
        """
        self.brain = brain
        self.max_param = max_param
        self.params = None
        self.count_oscillators = None
        self.periods = None
        self.phase_offsets = None
        self.amplitudes = None
        # Average Period
        self.avg_period = None
        # Deviation of Period
        self.dev_period = None
        # Average Phase Offset
        self.avg_phase_offset = None
        # Deviation of Phase Offset
        self.dev_phase_offset = None
        # Average Amplitude
        self.avg_amplitude = None
        # Deviation of Amplitude
        self.dev_amplitude = None
        # Average Intra-Deviation of Parameters
        self.avg_intra_dev_params = None
        # Average Inter-Deviation of Parameters
        self.avg_inter_dev_params = None
        # Sensors Reach
        self.sensors_reach = None
        # Recurrence
        self.recurrence = None
        # Synaptic Reception
        self.synaptic_reception = None
        self.collect_sets_of_params()

    def sigmoid(self, value):
        """
        Return sigmoid of value
        """
        return 1 / (1 + math.exp(-value))

    def set_measurements_to_zero(self):
        """
        Set all measurements to zero
        """
        self.avg_period = 0
        self.dev_period = 0
        self.avg_phase_offset = 0
        self.dev_phase_offset = 0
        self.avg_amplitude = 0
        self.dev_amplitude = 0
        self.avg_intra_dev_params = 0
        self.avg_inter_dev_params = 0
        self.sensors_reach = 0
        self.recurrence = 0
        self.synaptic_reception = 0

    def collect_sets_of_params(self):
        """
        Create lists of parameter values
        """
        if not isinstance(self.brain, BrainNN):
            logger.error('Brain not supported')
            return
        self.params = self.brain.params
        if self.params is not None:
            if self.periods is None:
                self.periods = [self.params[param].period for param in self.params]
            if self.phase_offsets is None:
                self.phase_offsets = [self.params[param].phase_offset for param in self.params]
            if self.amplitudes is None:
                self.amplitudes = [self.params[param].amplitude for param in self.params]

    def calc_count_oscillators(self):
        """
        Calculate amount of oscillators in brain
        """
        if not isinstance(self.brain, BrainNN):
            return
        oscillators = 0
        nodes = self.brain.nodes
        for node in nodes:
            if nodes[node].type == 'Oscillator':
                oscillators += 1
        self.count_oscillators = oscillators

    def measure_avg_period(self):
        """
        Measure average (median) Period among the oscillators of the controller
        """
        if self.params is None:
            self.avg_period = 0
            return self.avg_period
        if self.periods is None:
            self.collect_sets_of_params()
        median = np.median(self.periods) if self.periods else 0
        if median == 0 or self.max_param == 0:
            self.avg_period = 0
        else:
            self.avg_period = median / self.max_param
        return self.avg_period

    def measure_dev_period(self):
        """
        Measure standard deviation of Period among the oscillators of the controller
        """
        if self.params is None:
            self.dev_period = 0
            return self.dev_period
        if self.periods is None:
            self.collect_sets_of_params()
        self.dev_period = self.sigmoid(np.std(self.periods)) if self.periods else 0
        return self.dev_period

    def measure_avg_phase_offset(self):
        """
        Measure average (median) Phase Offset among the oscillators of the controller
        """
        if self.params is None:
            self.avg_phase_offset = 0
            return self.avg_phase_offset
        if self.phase_offsets is None:
            self.collect_sets_of_params()
        median = np.median(self.phase_offsets) if self.phase_offsets else 0
        if median == 0 or self.max_param == 0:
            self.avg_phase_offset = 0
        else:
            self.avg_phase_offset = median / self.max_param
        return self.avg_phase_offset

    def measure_dev_phase_offset(self):
        """
        Measure standard deviation of Phase Offset among the oscillators of the controller
        """
        if self.params is None:
            self.dev_phase_offset = 0
            return self.dev_phase_offset
        if self.phase_offsets is None:
            self.collect_sets_of_params()
        self.dev_phase_offset = self.sigmoid(np.std(self.phase_offsets)) if self.phase_offsets else 0
        return self.dev_phase_offset

    def measure_avg_amplitude(self):
        """
        Measure average (median) Amplitude among the oscillators of the controller
        """
        if self.params is None:
            self.avg_amplitude = 0
            return self.avg_amplitude
        if self.amplitudes is None:
            self.collect_sets_of_params()
        median = np.median(self.amplitudes) if self.amplitudes else 0
        if median == 0 or self.max_param == 0:
            self.avg_amplitude = 0
        else:
            self.avg_amplitude = median / self.max_param
        return self.avg_amplitude

    def measure_dev_amplitude(self):
        """
        Measure standard deviation of Amplitude among the oscillators of the controller
        """
        if self.params is None:
            self.dev_amplitude = 0
            return self.dev_amplitude
        if self.amplitudes is None:
            self.collect_sets_of_params()
        self.dev_amplitude = self.sigmoid(np.std(self.amplitudes)) if self.amplitudes else 0
        return self.dev_amplitude

    def measure_avg_intra_dev_params(self):
        """
        Describes the average (median) among the oscillators, regarding the standard deviation of Period, Phase Offset, and Amplitude,
        """
        if self.params is None:
            self.avg_intra_dev_params = 0
            return self.avg_intra_dev_params
        params = self.params
        dt = [np.std([params[param].period, params[param].phase_offset, params[param].amplitude]) for param in params] if params else 0
        self.avg_intra_dev_params = self.sigmoid(np.median(dt)) if dt else 0
        return self.avg_intra_dev_params

    def measure_avg_inter_dev_params(self):
        """
        Measure average (mean) of the parameters Period, Phase Offset, and Amplitude, regarding their deviations among the oscillator
        """
        if self.params is None:
            self.avg_inter_dev_params = 0
            return self.avg_inter_dev_params
        if self.periods is None or self.phase_offsets is None or self.amplitudes is None:
            self.collect_sets_of_params()
        periods_std = np.std(self.periods) if self.periods else 0
        p_offset_std = np.std(self.phase_offsets) if self.phase_offsets else 0
        amplitude_std = np.std(self.amplitudes) if self.amplitudes else 0
        self.avg_inter_dev_params = self.sigmoid((periods_std + p_offset_std + amplitude_std) / 3)
        return self.avg_inter_dev_params

    def measure_sensors_reach(self):
        """
        Describes how connected the sensors are to the oscillators
        """
        if self.params is None:
            self.sensors_reach = 0
            return self.sensors_reach
        if self.count_oscillators is None:
            self.calc_count_oscillators()

        connections = []
        nodes = self.brain.nodes
        # TODO REMOVE condition WHEN duplicated nodes bug is fixed -- duplicated nodes end in '-[0-9]+' or '-core[0-9]+' (node2-2, node2-core1)
        duplicates = fnmatch.filter(nodes, 'node*-*')
        for node in nodes:
            if node not in duplicates and nodes[node].type == 'Input':
                connections_of_node = 0
                for connection in self.brain.connections:
                    if connection.src == nodes[node].id:
                        connections_of_node += 1
                if connections_of_node == 0 or self.count_oscillators == 0:
                    connections.append(0)
                else:
                    connections.append(connections_of_node/self.count_oscillators)
        if not connections:
            self.sensors_reach = 0
            return self.sensors_reach
        self.sensors_reach = np.median(connections) if connections else 0
        return self.sensors_reach

    def measure_recurrence(self):
        """
        Describes the proportion of oscillators that have a recurrent connection
        """
        if self.params is None:
            self.recurrence = 0
            return self.recurrence
        connections = self.brain.connections
        recurrent = 0
        for connection in connections:
            if connection.src == connection.dst:
                recurrent += 1

        if self.count_oscillators is None:
            self.calc_count_oscillators()

        if recurrent == 0 or self.count_oscillators == 0:
            self.recurrence = 0
            return self.recurrence
        else:
            self.recurrence = recurrent/self.count_oscillators

        return self.recurrence

    def measure_synaptic_reception(self):
        """
        Describes the average (median) balance between inhibitory and excitatory connections from the sensors to the oscillators in the controller
        """
        if self.params is None:
            self.synaptic_reception = 0
            return self.synaptic_reception
        balance_set = []
        nodes = self.brain.nodes
        connections = self.brain.connections
        for node in nodes:
            if nodes[node].type == 'Oscillator':
                inhibitory = []
                excitatory = []
                for connection in connections:
                    if connection.dst == nodes[node].id and connection.src != nodes[node].id:
                        if connection.weight < 0:
                            inhibitory.append(abs(connection.weight))
                        if connection.weight > 0:
                            excitatory.append(connection.weight)
                inhibitory_sum = np.sum(inhibitory) if inhibitory else 0
                excitatory_sum = np.sum(excitatory) if excitatory else 0
                min_value = min(inhibitory_sum, excitatory_sum)
                max_value = max(inhibitory_sum, excitatory_sum)
                if min_value == 0 or max_value == 0:
                    balance_set.append(0)
                else:
                    balance_set.append(min_value / max_value)
        self.synaptic_reception = np.median(balance_set) if balance_set else 0
        return self.synaptic_reception

    def measure_all(self):
        """
        Perform all brain measurements
        """
        if not isinstance(self.brain, BrainNN):
            self.set_measurements_to_zero()
            raise RuntimeError('Brain not supported')
        self.calc_count_oscillators()
        self.measure_avg_period()
        self.measure_dev_period()
        self.measure_avg_phase_offset()
        self.measure_dev_phase_offset()
        self.measure_avg_amplitude()
        self.measure_dev_amplitude()
        self.measure_avg_intra_dev_params()
        self.measure_avg_inter_dev_params()
        self.measure_sensors_reach()
        self.measure_recurrence()
        self.measure_synaptic_reception()

    def set_all_zero(self):
        self.avg_period = 0
        self.dev_period = 0
        self.avg_phase_offset = 0
        self.dev_phase_offset = 0
        self.avg_amplitude = 0
        self.dev_amplitude = 0
        self.avg_intra_dev_params = 0
        self.avg_inter_dev_params = 0
        self.sensors_reach = 0
        self.recurrence = 0
        self.synaptic_reception = 0

    def measurements_to_dict(self):
        """
        Return measurements as dictionary
        """
        return {
            'avg_period': self.avg_period,
            'dev_period': self.dev_period,
            'avg_phase_offset': self.avg_phase_offset,
            'dev_phase_offset': self.dev_phase_offset,
            'avg_amplitude': self.avg_amplitude,
            'dev_amplitude': self.dev_amplitude,
            'avg_intra_dev_params': self.avg_intra_dev_params,
            'avg_inter_dev_params': self.avg_inter_dev_params,
            'sensors_reach': self.sensors_reach,
            'recurrence': self.recurrence,
            'synaptic_reception': self.synaptic_reception
        }

    def __repr__(self):
        return self.measurements_to_dict().__repr__()