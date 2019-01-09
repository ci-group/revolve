from __future__ import absolute_import

from pyrevolve.build.sdf import RobotBuilder, BodyBuilder, NeuralNetBuilder, BasicBattery
from pyrevolve.angle.robogen.util import apply_surface_parameters
from pyrevolve.sdfbuilder import SDF
from ..spec import get_body_spec, get_brain_spec


def get_builder(conf):
    """
    :param conf:
    :return:
    """
    body_spec = get_body_spec(conf)
    brain_spec = get_brain_spec(conf)
    return RobotBuilder(
            body_builder=BodyBuilder(body_spec, conf),
            brain_builder=NeuralNetBuilder(brain_spec)
    )


def get_simulation_robot(
        robot,
        name,
        builder,
        conf,
        battery_charge=None
):
    """
    :param robot:
    :param name:
    :param builder:
    :param conf: Config
    :param battery_charge:
    :return:
    """
    battery = None if battery_charge is None else BasicBattery(battery_charge)
    brain_conf = None if not hasattr(conf, 'brain_conf') else conf.brain_conf

    model = builder.get_sdf_model(
            robot=robot,
            controller_plugin="libRobotControlPlugin.so",
            update_rate=conf.controller_update_rate,
            name=name,
            battery=battery,
            brain_conf=brain_conf
    )

    apply_surface_parameters(model, conf.world_step_size)

    sdf = SDF()
    sdf.add_element(model)
    return sdf
