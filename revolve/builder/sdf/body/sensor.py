from sdfbuilder.base import Element


class Sensor(Element):
    """
    Sensor base class
    """
    # SDF tag name, should not be changed in subclass
    TAG_NAME = 'rv:sensor'

    # Should be a sensible default for most sensors
    OUTPUT_NEURONS = 1