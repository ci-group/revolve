import unittest
import os

import pyrevolve.revolve_bot
import pyrevolve.genotype.plasticoding

LOCAL_FOLDER = os.path.dirname(__file__)


class TestPlastiCoding(unittest.TestCase):
    def setUp(self):
        self.conf = pyrevolve.genotype.plasticoding.PlasticodingConfig(
            allow_vertical_brick=False,
            use_movement_commands=True,
            use_rotation_commands=False,
            use_movement_stack=False,
        )
        self.genotype = pyrevolve.genotype.plasticoding.initialization.random_initialization(self.conf, 176)

    def test_development(self):
        robot = self.genotype.develop()

    def test_substrate(self):
        robot = self.genotype.develop()
        robot.update_substrate(raise_for_intersections=True)

    def test_measure_body(self):
        robot = self.genotype.develop()
        robot.measure_body()

    def test_measure_brain(self):
        robot = self.genotype.develop()
        robot.measure_brain()

    def test_read_write_file(self):
        file1 = '/tmp/test_genotype.txt'
        file2 = '/tmp/test_genotype2.txt'

        self.genotype.export_genotype(file1)

        genotype2 = pyrevolve.genotype.plasticoding.Plasticoding(self.conf, self.genotype.id)
        genotype2.id = self.genotype.id
        genotype2.load_genotype(file1)
        genotype2.export_genotype(file2)

        file1_txt = open(file1)
        file2_txt = open(file2)

        self.assertListEqual(file1_txt.readlines(), file2_txt.readlines())

        file1_txt.close()
        file2_txt.close()

    def test_collision(self):
        genotype_180 = pyrevolve.genotype.plasticoding.Plasticoding(self.conf, 180)
        genotype_180.load_genotype(os.path.join(LOCAL_FOLDER, 'genotype_180.txt'))
        robot = genotype_180.develop()
        robot.update_substrate(raise_for_intersections=True)


class Test176(unittest.TestCase):
    def setUp(self):
        self.conf = pyrevolve.genotype.plasticoding.PlasticodingConfig(
            allow_vertical_brick=False,
            use_movement_commands=True,
            use_rotation_commands=False,
            use_movement_stack=False,
        )

        _id = 176
        self.genotype = pyrevolve.genotype.plasticoding.Plasticoding(self.conf, _id)
        self.genotype.load_genotype(os.path.join(LOCAL_FOLDER, 'genotype_176.txt'))

        self.robot = self.genotype.develop()

    def test_measurements_body(self):
        branching = 0.333
        connectivity1 = 0.625
        connectivity1_abs = 5
        connectivity2 = 0.444
        connectivity2_abs = 4
        connectivity3 = 1
        connectivity4 = 1
        connectivity5 = 1
        coverage = 0.44
        effective_joints = 0.444
        joints_abs = 6
        length_ratio = 1
        sensors = 0.2
        symmetry = 0.667
        total_components = 0.11
        total_components_abs = 11

        self.robot.render_body('/tmp/robot_body.png')
        self.genotype.export_genotype('/tmp/genotype.txt')

        m = self.robot.measure_body()
        self.assertAlmostEqual(branching, m.branching, 3)
        self.assertAlmostEqual(connectivity1, m.limbs, 3)
        self.assertAlmostEqual(connectivity1_abs, m.extremities, 3)
        self.assertAlmostEqual(connectivity2, m.length_of_limbs, 3)
        self.assertAlmostEqual(connectivity2_abs, m.extensiveness, 3)
        # self.assertAlmostEqual(connectivity3, m., 3)
        self.assertAlmostEqual(connectivity4, m.branching_modules_count, 3)
        self.assertAlmostEqual(connectivity5, m.tx_branching_modules_count, 3)
        self.assertAlmostEqual(coverage, m.coverage, 3)
        self.assertAlmostEqual(effective_joints, m.joints, 3)
        self.assertAlmostEqual(joints_abs, m.hinge_count, 3)
        self.assertAlmostEqual(length_ratio, m.proportion, 3)
        self.assertAlmostEqual(sensors, m.sensors, 3)
        self.assertAlmostEqual(symmetry, m.symmetry, 3)
        # self.assertAlmostEqual(total_components, m.size, 3)
        self.assertAlmostEqual(total_components_abs, m.absolute_size, 3)

    def test_measurements_brain(self):
        amplitude_average = 0.551664
        amplitude_deviation = 0.915769767
        inputs_reach = 0.583333
        inter_params_dev_average = 0.8811009266695952
        intra_params_dev_average = 0.8187877255612809
        offset_average = 0.37370865000000003
        offset_deviation = 0.857319047568582
        period_average = 0.25102035
        period_deviation = 0.8616760913682427
        recurrence = 0.5
        synaptic_reception = 0

        self.robot.render_brain('/tmp/robot_brain.png')

        m = self.robot.measure_brain()
        self.assertAlmostEqual(amplitude_average, m.avg_amplitude, 3)
        self.assertAlmostEqual(amplitude_deviation, m.dev_amplitude, 3)
        self.assertAlmostEqual(inputs_reach, m.sensors_reach, 3)
        self.assertAlmostEqual(inter_params_dev_average, m.avg_inter_dev_params, 3)
        self.assertAlmostEqual(intra_params_dev_average, m.avg_intra_dev_params, 3)
        self.assertAlmostEqual(offset_average, m.avg_phase_offset, 3)
        self.assertAlmostEqual(offset_deviation, m.dev_phase_offset, 3)
        self.assertAlmostEqual(period_average, m.avg_period, 3)
        self.assertAlmostEqual(period_deviation, m.dev_period, 3)
        self.assertAlmostEqual(recurrence, m.recurrence, 3)
        self.assertAlmostEqual(synaptic_reception, m.synaptic_reception, 3)

    def test_measurements_brain_pdf(self):
        amplitude_average = 0.551664
        amplitude_deviation = 0.915769767
        inputs_reach = 0.583333
        inter_params_dev_average = 0.8811009266695952
        intra_params_dev_average = 0.8187877255612809
        offset_average = 0.37370865000000003
        offset_deviation = 0.857319047568582
        period_average = 0.25102035
        period_deviation = 0.8616760913682427
        recurrence = 0.5
        synaptic_reception = 0

        self.robot.render_brain('/tmp/robot_brain.pdf')

        m = self.robot.measure_brain()
        self.assertAlmostEqual(amplitude_average, m.avg_amplitude, 3)
        self.assertAlmostEqual(amplitude_deviation, m.dev_amplitude, 3)
        self.assertAlmostEqual(inputs_reach, m.sensors_reach, 3)
        self.assertAlmostEqual(inter_params_dev_average, m.avg_inter_dev_params, 3)
        self.assertAlmostEqual(intra_params_dev_average, m.avg_intra_dev_params, 3)
        self.assertAlmostEqual(offset_average, m.avg_phase_offset, 3)
        self.assertAlmostEqual(offset_deviation, m.dev_phase_offset, 3)
        self.assertAlmostEqual(period_average, m.avg_period, 3)
        self.assertAlmostEqual(period_deviation, m.dev_period, 3)
        self.assertAlmostEqual(recurrence, m.recurrence, 3)
        self.assertAlmostEqual(synaptic_reception, m.synaptic_reception, 3)
