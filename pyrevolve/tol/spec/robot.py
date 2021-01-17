from __future__ import absolute_import

from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from ..spec.body import get_body_generator


def get_tree_generator(conf):
    """
    :param conf:
    :return:
    :rtype: TreeGenerator
    """
    body_gen = get_body_generator(conf)
    #brain_gen = get_brain_generator(conf)
    return RobogenTreeGenerator(body_gen, None, conf)
