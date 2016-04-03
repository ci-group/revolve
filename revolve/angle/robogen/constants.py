"""
ToL constants
"""
from __future__ import absolute_import
import math
from ...build.sdf import PID

MAX_SERVO_TORQUE = 1.8 * 9.81 / 100
""" Expressed in Newton*m from kg-cm = ((kg-cm)*g)/100 """

MAX_SERVO_TORQUE_ROTATIONAL = 4 * 9.81 / 100
""" Expressed in Newton*m from kg-cm = ((kg-cm)*g)/100 """

MAX_SERVO_VELOCITY = (50.0/60.0) * 2 * math.pi
""" Maximum rotational velocity of a servo, in radians / second """

SERVO_LIMIT = math.radians(45)
""" Upper and lower limit """

HINGE_LIMIT = math.radians(45)
""" Upper and lower limit for hinge """

CARDAN_LIMIT = math.radians(45)
""" Upper and lower limit of each axis of rotation """

SERVO_VELOCITY_PID = PID(
    proportional_gain=0.5,
    derivative_gain=0.0,
    integral_gain=0,
    integral_max=0
)
""" Default servo velocity PID. **Currently unused** as velocity is abstractly set
    on the servo. """

SERVO_POSITION_PID = PID(
    proportional_gain=0.9,
    derivative_gain=0,
    integral_gain=0,
    integral_max=0
)
""" Default servo position PID. """

# Original parameter values from RobogenCollision.cpp
SURFACE_FRICTION1 = 1.0
SURFACE_FRICTION2 = 1.0
SURFACE_SLIP1 = 0.01
SURFACE_SLIP2 = 0.01

# soft_erp / soft_cfm for surfaces cannot be set directly
# in Gazebo, so they are calculated into kp and kd here using
# the step size and the intended values. Make sure to change
# them when you change simulation parameters (and change
# them in `tol_ground` as well).
SURFACE_ERP = 0.1
SURFACE_CFM = 10e-6
INTENDED_STEP_SIZE = 0.005
