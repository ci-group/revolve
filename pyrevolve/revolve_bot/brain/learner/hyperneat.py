import sys
import xml.etree.ElementTree
import multineat
from .base import Learner

class HyperNEATLearner(Learner):
    TYPE = 'hyperneat'

    def __init__(self):
        self.params = multineat.Parameters()
        # self.to_yaml()



    def to_yaml(self):
        obj = super().to_yaml()
        obj['learner']['hyperneat'] = self.params
        return obj

    @staticmethod
    def from_yaml(yaml_object):
        HyperNL = HyperNEATLearner()
        for yaml_params in ["params"]:
            try:
                my_object = yaml_object[yaml_params]
                for key, value in my_object.items():
                    try:
                        setattr(HyperNL.params, key, value)
                    except:
                        print("Couldn't set {}, {}", format(key, value))
            except:
                print("Didn't load {} parameters".format(yaml_params))

        return HyperNL

    def learner_sdf(self):
        learner = xml.etree.ElementTree.Element('rv:learner', {
            'type': 'hyperneat',
        })
        learner.append(self.params_sdf())
        return learner

    def params_sdf(self):
        assert(self.params is not None)

        element = xml.etree.ElementTree.Element('rv:params', {
            'PopulationSize': str(self.params.PopulationSize),
            'DynamicCompatibility': str(self.params.DynamicCompatibility),
            'NormalizeGenomeSize': str(self.params.NormalizeGenomeSize),
            'WeightDiffCoeff': str(self.params.WeightDiffCoeff),
            'CompatTreshold': str(self.params.CompatTreshold),
            'YoungAgeTreshold': str(self.params.YoungAgeTreshold),
            # 'SpeciesMaxStagnation ': str(self.params.SpeciesMaxStagnation), # Not present in multineat.Population()?
            'OldAgeTreshold': str(self.params.OldAgeTreshold),
            'MinSpecies': str(self.params.MinSpecies),
            'MaxSpecies': str(self.params.MaxSpecies),
            'RouletteWheelSelection': str(self.params.RouletteWheelSelection),
            'RecurrentProb': str(self.params.RecurrentProb),
            'OverallMutationRate': str(self.params.OverallMutationRate),
            'ArchiveEnforcement': str(self.params.ArchiveEnforcement),
            'MutateWeightsProb': str(self.params.MutateWeightsProb),
            'WeightMutationMaxPower': str(self.params.WeightMutationMaxPower),
            'WeightReplacementMaxPower': str(self.params.WeightReplacementMaxPower),
            'MutateWeightsSevereProb': str(self.params.MutateWeightsSevereProb),
            'WeightMutationRate': str(self.params.WeightMutationRate),
            'WeightReplacementRate': str(self.params.WeightReplacementRate),
            'MaxWeight': str(self.params.MaxWeight),
            'MutateAddNeuronProb': str(self.params.MutateAddNeuronProb),
            'MutateAddLinkProb': str(self.params.MutateAddLinkProb),
            'MutateRemLinkProb': str(self.params.MutateRemLinkProb),
            'MinActivationA': str(self.params.MinActivationA),
            'MaxActivationA': str(self.params.MaxActivationA),
            'ActivationFunction_SignedSigmoid_Prob': str(self.params.ActivationFunction_SignedSigmoid_Prob),
            'ActivationFunction_UnsignedSigmoid_Prob': str(self.params.ActivationFunction_UnsignedSigmoid_Prob),
            'ActivationFunction_Tanh_Prob': str(self.params.ActivationFunction_Tanh_Prob),
            'ActivationFunction_SignedStep_Prob': str(self.params.ActivationFunction_SignedStep_Prob),
            'CrossoverRate': str(self.params.CrossoverRate),
            'MultipointCrossoverRate': str(self.params.MultipointCrossoverRate),
            'SurvivalRate': str(self.params.SurvivalRate),
            'MutateNeuronTraitsProb': str(self.params.MutateNeuronTraitsProb),
            'MutateLinkTraitsProb': str(self.params.MutateLinkTraitsProb),
            'AllowLoops': str(self.params.AllowLoops),
            'AllowClones': str(self.params.AllowClones),
        })
        return element



