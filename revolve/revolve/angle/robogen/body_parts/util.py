

class ColorMixin(object):
    """
    Mixin class for "colorable" parts. Needs to be mixed
    in with a body part, or it won't work.
    """

    def apply_color(self):
        """
        Applies the "red", "green" and "blue" arguments
        to all links in this body part.
        """
        red = self.part_params.get("red", 0.5)
        green = self.part_params.get("green", 0.5)
        blue = self.part_params.get("blue", 0.5)
        self.make_color(red, green, blue)