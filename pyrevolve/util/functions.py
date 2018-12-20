from __future__ import absolute_import

import random


def decide(probability):
    """
    Returns `True` with the given probability
    :param probability: Probability between 0 and 1
    :type probability: float
    :return:
    """
    return random.random() < probability
