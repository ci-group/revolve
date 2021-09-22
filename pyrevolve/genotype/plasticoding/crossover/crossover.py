class CrossoverConfig:
    def __init__(self,
                 crossover_prob, plasticoding_config):
        """
        Creates a Crossover object that sets the configuration for the crossover operator

        :param crossover_prob: crossover probability
        """
        self.crossover_prob = crossover_prob
        self.plasticoding_config = plasticoding_config
