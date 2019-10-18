import random
import math

from pyrevolve.custom_logging.logger import logger
from pyrevolve.genotype import Genotype
from pyrevolve.genotype.plasticoding.alphabet import Alphabet, INDEX_SYMBOL, INDEX_PARAMS
from pyrevolve.genotype.plasticoding.decoder import GrammarExpander
from pyrevolve.revolve_bot.brain.brain_nn import Node


class Plasticoding(Genotype):
    """
    L-system genotypic representation, enhanced with epigenetic capabilities for phenotypic plasticity, through Genetic Programming.
    """

    def __init__(self, conf, robot_id):
        """
        :param conf: configurations for lsystem
        :param robot_id: unique id of the robot
        :type conf: PlasticodingConfig
        """
        self.conf = conf
        self.id = str(robot_id)
        self.grammar = {}

        # Auxiliary variables
        self.valid = False
        self.intermediate_phenotype = None
        self.phenotype = None

    def load_genotype(self, genotype_file):
        with open(genotype_file) as f:
            lines = f.readlines()
            self._load_genotype_from(lines)

    def _load_genotype_from(self, lines):
        for line in lines:
            line_array = line.split(' ')
            replaceable_symbol = Alphabet(line_array[0])
            self.grammar[replaceable_symbol] = []
            rule = line_array[1:len(line_array) - 1]
            for symbol_array in rule:
                symbol_array = symbol_array.split('_')
                symbol = Alphabet(symbol_array[0])
                if len(symbol_array) > 1:
                    params = symbol_array[1].split('|')
                else:
                    params = []
                self.grammar[replaceable_symbol].append([symbol, params])

    def export_genotype(self, filepath):
        with open(filepath, 'w+') as file:
            self._export_genotype_open_file(file)

    def _export_genotype_open_file(self, file):
        for key, rule in self.grammar.items():
            line = key.value + ' '
            for item_rule in range(0, len(rule)):
                symbol = rule[item_rule][INDEX_SYMBOL].value
                if len(rule[item_rule][INDEX_PARAMS]) > 0:
                    params = '_'
                    for param in range(0, len(rule[item_rule][INDEX_PARAMS])):
                        params += str(rule[item_rule][INDEX_PARAMS][param])
                        if param < len(rule[item_rule][INDEX_PARAMS]) - 1:
                            params += '|'
                    symbol += params
                line += symbol + ' '
            file.write(line + '\n')

    def check_validity(self):
        if self.phenotype._morphological_measurements.measurement_to_dict()['hinge_count'] > 0:
            self.valid = True

    def develop(self):
        self.phenotype = GrammarExpander(self)\
            .expand_grammar(self.conf.i_iterations, self.conf.axiom_w)\
            .decode_sentence()
        return self.phenotype

    @staticmethod
    def build_symbol(symbol, conf):
        """
        Adds params for alphabet symbols (when it applies).
        :return:
        """
        if type(symbol) is Alphabet:
            symbol = Alphabet.wordify(symbol)

        if symbol[INDEX_SYMBOL] is Alphabet.JOINT_HORIZONTAL \
                or symbol[INDEX_SYMBOL] is Alphabet.JOINT_VERTICAL:
            symbol[INDEX_PARAMS].clear()
            symbol[INDEX_PARAMS].extend(
                [random.uniform(conf.weight_min, conf.weight_max),
                 random.uniform(conf.oscillator_param_min, conf.oscillator_param_max),
                 random.uniform(conf.oscillator_param_min, conf.oscillator_param_max),
                 random.uniform(conf.oscillator_param_min, conf.oscillator_param_max)]
            )

        if symbol[INDEX_SYMBOL] is Alphabet.SENSOR \
                or symbol[INDEX_SYMBOL] is Alphabet.ADD_EDGE \
                or symbol[INDEX_SYMBOL] is Alphabet.LOOP:
            symbol[INDEX_PARAMS].clear()
            symbol[INDEX_PARAMS].append(random.uniform(conf.weight_min, conf.weight_max))

        if symbol[INDEX_SYMBOL] is Alphabet.MUTATE_EDGE \
                or symbol[INDEX_SYMBOL] is Alphabet.MUTATE_AMP \
                or symbol[INDEX_SYMBOL] is Alphabet.MUTATE_PER \
                or symbol[INDEX_SYMBOL] is Alphabet.MUTATE_OFF:
            symbol[INDEX_PARAMS].clear()
            symbol[INDEX_PARAMS].append(random.normalvariate(0, 1))

        if symbol[INDEX_SYMBOL] is Alphabet.MOVE_REF_S \
                or symbol[INDEX_SYMBOL] is Alphabet.MOVE_REF_O:
            intermediate_temp = random.normalvariate(0, 1)
            final_temp = random.normalvariate(0, 1)
            symbol[INDEX_PARAMS].clear()
            symbol[INDEX_PARAMS].append(math.ceil(math.sqrt(math.pow(intermediate_temp, 2))))
            symbol[INDEX_PARAMS].append(math.ceil(math.sqrt(math.pow(final_temp, 2))))

        return symbol


class NodeExtended(Node):
    def __init__(self):
        super().__init__()
        self.weight = None
        self.input_nodes = []
        self.output_nodes = []
        self.params = None
