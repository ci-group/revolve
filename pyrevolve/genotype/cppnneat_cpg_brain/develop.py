from xml.etree import ElementTree

import multineat
from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype
from pyrevolve.genotype.cppnneat_cpg_brain.config import CppnneatCpgBrainConfig
from pyrevolve.revolve_bot.brain import Brain
from pyrevolve.revolve_bot.brain.cpg_target import BrainCPGTarget
from pyrevolve.revolve_bot.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.revolve_module import CoreModule


def cppnneat_cpg_brain_develop(
    genotype: CppnneatGenotype, config: CppnneatCpgBrainConfig, body: CoreModule
) -> Brain:
    brain = BrainCPGTarget()
    brain.abs_output_bound = config.abs_output_bound
    brain.use_frame_of_reference = config.use_frame_of_reference
    brain.output_signal_factor = config.output_signal_factor
    brain.range_ub = config.range_ub
    brain.init_neuron_state = config.init_neuron_state
    brain.reset_neuron_random = config.reset_neuron_random

    # Convert to sdf so we can extract things like position and order of actuators exactly like they would be read by the plugin
    bot = RevolveBot("dummy")
    bot._body = body
    bot._brain = BrainCPGTarget()  # dummy
    bot.update_substrate()
    sdf = bot.to_sdf()
    root = ElementTree.fromstring(sdf)
    namespaces = {"rv": "https://github.com/ci-group/revolve"}
    actuators = root.findall(
        "model/plugin[@name='robot_controller']/rv:robot_config/rv:brain/rv:actuators/rv:servomotor",
        namespaces,
    )

    # calculate weights from actuators
    brain.weights = []

    brain_net = multineat.NeuralNetwork()
    genotype.multineat_genome.BuildPhenotype(brain_net)

    parsecoords = lambda coordsstr: list(map(lambda x: float(x), coordsstr.split(";")))

    # internal weights
    for actuator in actuators:
        coords = parsecoords(actuator.attrib["coordinates"])
        brain_net.Input(
            [1.0, coords[0], coords[1], coords[2], coords[0], coords[1], coords[2]]
        )  # 1.0 is the bias input
        brain_net.Activate()
        weight = brain_net.Output()[0]
        brain.weights.append(weight)

    # external weights
    for i, actuator in enumerate(actuators[:-1]):
        for neighbour in actuators[i + 1 :]:
            leftcoords = parsecoords(actuator.attrib["coordinates"])
            rightcoords = parsecoords(neighbour.attrib["coordinates"])
            if (
                abs(leftcoords[0] - rightcoords[0])
                + abs(leftcoords[1] - rightcoords[1])
                + abs(leftcoords[2] - rightcoords[2])
                < 2.01
            ):
                brain_net.Input(
                    [
                        1.0,
                        leftcoords[0],
                        leftcoords[1],
                        leftcoords[2],
                        rightcoords[0],
                        rightcoords[1],
                        rightcoords[2],
                    ]
                )
                brain_net.Activate()
                weight = brain_net.Output()[0]
                brain.weights.append(weight)

    return brain
