import unittest
import os

import pyrevolve.revolve_bot
import pyrevolve.genotype.plasticoding.plasticoding


class TestPlastiCoding(unittest.TestCase):
    def setUp(self):
        self.conf = pyrevolve.genotype.plasticoding.plasticoding.PlasticodingConfig()
        self.genotype = pyrevolve.genotype.plasticoding.plasticoding.initialization.random_initialization(self.conf)

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

    def test_collision(self):
        genotype_180 = pyrevolve.genotype.plasticoding.plasticoding.Plasticoding(self.conf)
        genotype_180.id = 180
        genotype_180.load_genotype(os.path.join(os.path.dirname(__file__), 'genotype_'))
        robot = genotype_180.develop()
        robot.update_substrate(raise_for_intersections=True)


class Test180(unittest.TestCase):
    def setUp(self):
        self.conf = pyrevolve.genotype.plasticoding.plasticoding.PlasticodingConfig()

        self.genotype = pyrevolve.genotype.plasticoding.plasticoding.Plasticoding(self.conf)
        self.genotype.id = 176
        self.genotype.load_genotype(os.path.join(os.path.dirname(__file__), 'genotype_'))

        self.robot = self.genotype.develop()

    def test_measurements_body(self):
        branching = 0.333
        connectivity1 = 0.625
        connectivity1_abs = 5
        connectivity2 = 0.444
        connectivity2_abs = 4
        connectivity3 = 1
        connectivity4 = 1
        coverage = 0.44
        effective_joints = 0.444
        joints_abs = 6
        length_ratio = 1
        sensors = 0.2
        symmetry = 0.667
        total_components = 0.11
        total_components_abs = 11

        m = self.robot.measure_body()
        self.assertAlmostEqual(branching, m.branching)
        self.assertAlmostEqual(connectivity1, m.limbs)
        self.assertAlmostEqual(connectivity1_abs, m.extremities)
        self.assertAlmostEqual(connectivity2, m.length_of_limbs)
        self.assertAlmostEqual(connectivity2_abs, m.extensiveness)
        # self.assertAlmostEqual(connectivity3, m.)
        self.assertAlmostEqual(connectivity4, m.branching_modules_count)
        self.assertAlmostEqual(coverage, m.coverage)
        self.assertAlmostEqual(effective_joints, m.joints)
        self.assertAlmostEqual(joints_abs, m.hinge_count)
        self.assertAlmostEqual(length_ratio, m.proportion)
        self.assertAlmostEqual(sensors, m.sensors)
        self.assertAlmostEqual(symmetry, m.symmetry)
        self.assertAlmostEqual(total_components, m.size)
        self.assertAlmostEqual(total_components_abs, m.absolute_size)

    def test_measurements_brain(self):
        amplitude_average = 0.551664
        amplitude_deviation = 0.914862
        inputs_reach = 0.583333
        inter_params_dev_average = 0.875401
        intra_params_dev_average = 0.791891
        offset_average = 0.355431
        offset_deviation = 0.852846
        period_average = 0.258451
        period_deviation = 0.847762
        recurrence = 0.5
        synaptic_reception = 0

        m = self.robot.measure_brain()
        self.assertAlmostEqual(amplitude_average, m.avg_amplitude)
        self.assertAlmostEqual(amplitude_deviation, m.dev_amplitude)
        self.assertAlmostEqual(inputs_reach, m.sensors_reach)
        self.assertAlmostEqual(inter_params_dev_average, m.avg_inter_dev_params)
        self.assertAlmostEqual(intra_params_dev_average, m.avg_intra_dev_params)
        self.assertAlmostEqual(offset_average, m.avg_phase_offset)
        self.assertAlmostEqual(offset_deviation, m.dev_phase_offset)
        self.assertAlmostEqual(period_average, m.avg_period)
        self.assertAlmostEqual(period_deviation, m.dev_period)
        self.assertAlmostEqual(recurrence, m.recurrence)
        self.assertAlmostEqual(synaptic_reception, m.synaptic_reception)
