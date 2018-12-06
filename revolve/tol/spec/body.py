from __future__ import absolute_import

from revolve.angle.robogen.spec import BodyGenerator
from revolve.angle.robogen.spec import get_body_spec as rv_body_spec
from random import gauss


class BodyGen(BodyGenerator):
    def choose_max_parts(self):
        return min(self.conf.max_parts,
                   max(self.conf.min_parts,
                       int(gauss(self.conf.initial_parts_mu,
                                 self.conf.initial_parts_sigma))))


def get_body_spec(conf):
    return rv_body_spec(conf)


def get_body_generator(conf):
    """
    Returns a body generator.

    :param conf:
    :return:
    """
    return BodyGen(conf)
