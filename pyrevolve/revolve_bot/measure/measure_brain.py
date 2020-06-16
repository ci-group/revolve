import numpy as np
import math
# belong to TODO
import fnmatch


class MeasureBrain:
    def __init__(self, brain, max_param):
        self.brain = brain
        self.max_param = max_param
        self.count_oscillators = None
        self.periods = None
        self.phase_offsets = None
        self.amplitudes = None
        self.avg_period = None
        self.dev_period = None
        self.avg_phase_offset = None
        self.dev_phase_offset = None
        self.avg_amplitude = None
        self.dev_amplitude = None
        self.avg_intra_dev_params = None
        self.avg_inter_dev_params = None
        self.sensors_reach = None
        self.recurrence = None
        self.synaptic_reception = None

    def sigmoid(self, value):
        """
        Return sigmoid of value
        """
        return 1 / (1 + math.exp(-value))

    def collect_sets_of_params(self):
        """
        Create lists of parameter values
        """
        params = self.brain.params
        if self.periods is None:
            self.periods = [params[param].period for param in params]
        if self.phase_offsets is None:
            self.phase_offsets = [params[param].phase_offset for param in params]
        if self.amplitudes is None:
            self.amplitudes = [params[param].amplitude for param in params]

    def calc_count_oscillators(self):
        """
        Calculate amount of oscillators in brain
        """
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
        if self.periods is None:
            self.collect_sets_of_params()
        median = np.median(self.periods)
        self.avg_period = median / self.max_param
        return self.avg_period

    def measure_dev_period(self):
        """
        Measure standard deviation of Period among the oscillators of the controller
        """
        if self.periods is None:
            self.collect_sets_of_params()
        self.dev_period = self.sigmoid(np.std(self.periods))
        return self.dev_period

    def measure_avg_phase_offset(self):
        """
        Measure average (median) Phase Offset among the oscillators of the controller
        """
        if self.phase_offsets is None:
            self.collect_sets_of_params()
        median = np.median(self.phase_offsets)
        self.avg_phase_offset = median / self.max_param
        return self.avg_phase_offset

    def measure_dev_phase_offset(self):
        """
        Measure standard deviation of Phase Offset among the oscillators of the controller
        """
        if self.phase_offsets is None:
            self.collect_sets_of_params()
        self.dev_phase_offset = self.sigmoid(np.std(self.phase_offsets))
        return self.dev_phase_offset

    def measure_avg_amplitude(self):
        """
        Measure average (median) Amplitude among the oscillators of the controller
        """
        if self.amplitudes is None:
            self.collect_sets_of_params()
        median = np.median(self.amplitudes)
        self.avg_amplitude = median / self.max_param
        return self.avg_amplitude

    def measure_dev_amplitude(self):
        """
        Measure standard deviation of Amplitude among the oscillators of the controller
        """
        if self.amplitudes is None:
            self.collect_sets_of_params()
        self.dev_amplitude = self.sigmoid(np.std(self.amplitudes))
        return self.dev_amplitude

    def measure_avg_intra_dev_params(self):
        """
        Describes the average (median) among the oscillators, regarding the standard deviation of Period, Phase Offset, and Amplitude,
        """
        params = self.brain.params
        dt = [np.std([params[param].period, params[param].phase_offset, params[param].amplitude]) for param in params]
        self.avg_intra_dev_params = self.sigmoid(np.median(dt))
        return self.avg_intra_dev_params

    def measure_avg_inter_dev_params(self):
        """
        Measure average (mean) of the parameters Period, Phase Offset, and Amplitude, regarding their deviations among the oscillator
        """
        if self.periods is None or self.phase_offsets is None or self.amplitudes is None:
            self.collect_sets_of_params()
        self.avg_inter_dev_params = self.sigmoid((np.std(self.periods) + np.std(self.phase_offsets) + np.std(self.amplitudes)) / 3)
        return self.avg_inter_dev_params

    def measure_sensors_reach(self):
        """
        Describes how connected the sensors are to the oscillators
        """
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
                connections.append(connections_of_node/self.count_oscillators)
        if not connections:
            self.sensors_reach = 0
            return 0
        self.sensors_reach = np.median(connections)
        return self.sensors_reach

    def measure_recurrence(self):
        """
        Describes the proportion of oscillators that have a recurrent connection
        """
        connections = self.brain.connections
        recurrent = 0
        for connection in connections:
            if connection.src == connection.dst:
                recurrent += 1

        if self.count_oscillators is None:
            self.calc_count_oscillators()

        if recurrent is 0:
            self.recurrence = 0
            return 0
        else:
            self.recurrence = recurrent/self.count_oscillators

        return self.recurrence

    def measure_synaptic_reception(self):
        """
        Describes the average (median) balance between inhibitory and excitatory connections from the sensors to the oscillators in the controller
        """
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
                inhibitory_sum = np.sum(inhibitory)
                excitatory_sum = np.sum(excitatory)
                min_value = min(inhibitory_sum, excitatory_sum)
                max_value = max(inhibitory_sum, excitatory_sum)
                if min_value == 0 or max_value == 0:
                    balance_set.append(0)
                else:
                    balance_set.append(min_value / max_value)
        self.synaptic_reception = np.median(balance_set)
        return self.synaptic_reception

    def measure_all(self):
        """
        Perform all brain measuerments
        """
        self.collect_sets_of_params()
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
        return self.measurements_to_dict()

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
