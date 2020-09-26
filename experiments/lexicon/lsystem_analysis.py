import os

import PIL
import imageio
from PIL import Image

from experiments.lexicon.population_lsystem_generation import _create_path
from pyrevolve.genotype.plasticoding import PlasticodingConfig, Plasticoding

# read genotype
INDEX_SYMBOL = 0
from pyrevolve.genotype.plasticoding.alphabet import Alphabet
from pyrevolve.genotype.plasticoding.decoder import GrammarExpander, PlasticodingDecoder
from pyrevolve.revolve_bot import RevolveBot


root_path = "output_blocks"
_create_path(root_path)

path = root_path + "/genotypes/"
robot_name = "genotype_{}.txt"

analyzed_path = root_path + "/analyzed"
_create_path(analyzed_path)
brain_output_path = analyzed_path + "/genotype_{}_iteration_{}_step_{}_brain"
body_output_path = analyzed_path + "/genotype_{}_iteration_{}_step_{}_body.png"

for robot_index in range(10):
        robot_index = robot_index + 1
        robot_genotype_path = os.path.join(path, robot_name.format(robot_index))

        # Create Plasticoding from file
        genotype_conf = PlasticodingConfig(
                max_structural_modules=40,
                allow_vertical_brick=False,
                use_movement_commands=True,
                use_rotation_commands=False,
                use_movement_stack=False,
            )

        plasticoding = Plasticoding(genotype_conf, robot_index-1)
        plasticoding.load_genotype(robot_genotype_path)

        number_of_iterations = 3

        grammar_expander = GrammarExpander(plasticoding)

        image_paths = []

        def export_phenotype(developed_sentence, iteration, step):

                # logger.info('Robot ' + str(self.id) + ' was early-developed.')
                phenotype = PlasticodingDecoder(grammar_expander._genotype.id, grammar_expander._conf,
                                                developed_sentence).decode_sentence()

                phenotype.render_body(body_output_path.format(robot_index, iteration, step))
                #phenotype.render_brain(brain_output_path.format(robot_index, iteration, step))
                image_paths.append(body_output_path.format(robot_index, iteration, step))
                iteration += 1


        developed_sentence = [(Alphabet.CORE_COMPONENT, [])]
        iteration = 0
        for i in range(0, number_of_iterations):

                position = 0
                print("iteration", i)
                index = 0
                for aux_index in range(0, len(developed_sentence)):
                        #print("aux ", aux_index)
                        symbol = developed_sentence[position][INDEX_SYMBOL]

                        # TODO check if is present in production rules instead, don't assume production rules and modules are
                        #  the same
                        if symbol in Alphabet.modules(grammar_expander._conf.allow_vertical_brick):
                                # removes symbol
                                print("replace " + str(symbol))
                                developed_sentence.pop(position)
                                # replaces by its production rule
                                ii = 0

                                for ii in range(0, len(grammar_expander._grammar[symbol])):
                                        developed_sentence.insert(position + ii, grammar_expander._grammar[symbol][ii])
                                        if grammar_expander._grammar[symbol][ii][0] in Alphabet.modules(grammar_expander._conf.allow_vertical_brick):
                                                print("inserting " + str(grammar_expander._grammar[symbol][ii][0]))
                                export_phenotype(developed_sentence, iteration, index)
                                index += 1

                                position = position + ii + 1
                        else:
                                position = position + 1

                iteration += 1

        max_x_size = 0
        max_y_size = 0
        images = []
        for image_path in image_paths:
                image = Image.open(image_path)
                if image.size[0] > max_x_size:
                        max_x_size = image.size[0]
                if image.size[1] > max_y_size:
                        max_y_size = image.size[1]

        print(max_x_size, max_y_size)
        for image_path in image_paths:
                image = Image.open(image_path)
                images.append(image.resize((max_x_size, max_y_size), Image.ANTIALIAS))


        imageio.mimwrite('output/robot_{}_movie.gif'.format(robot_index), images, fps=2)
        #images[0].save('output/robot_{}_movie.gif'.format(robot_index), save_all=True, append_images=images[1:], fps=1)