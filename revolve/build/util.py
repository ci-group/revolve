"""
Utility functions
"""
size_scale_factor = 1
weight_scale_factor = 1


def in_mm(x):
    return size_scale_factor * x / 1000.0


def in_cm(x):
    return size_scale_factor * x / 100.0


def in_grams(x):
    return weight_scale_factor * x / 1000.0
