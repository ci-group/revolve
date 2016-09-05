from math import ceil


class Time(object):
    """
    Time class like in Gazebo. Unlike Gazebo's though, we always
    use a positive number of nanoseconds, offset from a negative
    or positive number of seconds.
    """

    def __init__(self, sec=None, nsec=None, dbl=None, msg=None):
        """

        :return:
        """
        self.sec = 0
        self.nsec = 0
        self.set(sec, nsec, dbl, msg)

    def set(self, sec=None, nsec=None, dbl=None, msg=None):
        """
        Sets the time from either factor
        :param sec: Number of seconds
        :param nsec: Number of nanoseconds
        :param dbl: Double / float time value
        :param msg: Gazebo `Time` message
        :return:
        """
        if dbl is not None:
            self.sec = int(dbl)
            self.nsec = int(round((dbl - self.sec) * 10e9))
        elif msg:
            self.sec = msg.sec
            self.nsec = msg.nsec
        else:
            if sec is not None:
                self.sec = int(sec)

            if nsec is not None:
                self.nsec = int(nsec)

        self._correct()

    def _correct(self):
        """
        Corrects overflowing nanoseconds
        :return:
        """
        if self.nsec < 0:
            n = ceil(abs(self.nsec / float(10e9)))
            self.sec -= n
            self.nsec += n * 10e9
        elif self.nsec >= 10e9:
            n = int(self.nsec / 10e9)
            self.sec += n
            self.nsec -= n * 10e9

    def is_zero(self):
        """
        Check if this time is zero.
        :return:
        """
        return self.sec == 0 and self.nsec == 0

    def __eq__(self, other):
        """
        :param other:
        :return:
        """
        if isinstance(other, Time):
            return self.sec == other.sec and self.nsec == other.nsec
        else:
            return Time(dbl=other) == self

    def __ne__(self, other):
        """
        Inequality.
        :param other:
        :return:
        """
        return not self.__eq__(other)

    def __gt__(self, other):
        """
        Greater than
        :param other:
        :return:
        """
        return float(self) > float(other)

    def __lt__(self, other):
        """
        Smaller than
        :param other:
        :return:
        """
        return float(self) < float(other)

    def __ge__(self, other):
        """
        Greater than or equal to
        :param other:
        :return:
        """
        return float(self) >= float(other)

    def __le__(self, other):
        """
        Less than or equal to
        :param other:
        :return:
        """
        return float(self) <= float(other)

    def __add__(self, other):
        """
        Add two times
        :param other:
        :return:
        """
        if isinstance(other, Time):
            return self.__class__(self.sec + other.sec, self.nsec + other.nsec)

        # Otherwise assume a number
        return self.__class__(dbl=float(self) + other)

    __radd__ = __add__

    def __sub__(self, other):
        """
        Subtract two times
        :param other:
        :return:
        """
        if isinstance(other, Time):
            return self.__class__(self.sec - other.sec, self.nsec - other.nsec)

        # Assume a number
        return self.__class__(dbl=float(self) - other)

    def __rsub__(self, other):
        """
        :param other:
        :return:
        """
        # This would only be called if `other` is not a Time instance,
        # so assume the number version.
        return self.__class__(dbl=other - float(self))

    def __iadd__(self, other):
        """
        Internal add
        :param other:
        :return:
        """
        if isinstance(other, Time):
            self.set(self.sec + other.sec, self.nsec + other.nsec)
        else:
            self.set(dbl=float(self) + other)

        return self

    def __isub__(self, other):
        """
        Internal subtract
        :param other:
        :return:
        """
        if isinstance(other, Time):
            self.set(self.sec - other.sec, self.nsec - other.nsec)
        else:
            self.set(dbl=float(self) - other)

        return self

    def __neg__(self):
        """
        Negative of this time value
        :return:
        """
        return self.__class__(-self.sec, -self.nsec)

    def __float__(self):
        """
        Float / double representation of this time
        :return:
        """
        return self.sec + self.nsec / 10.0e9

    def __str__(self):
        return "%f" % float(self)

    __repr__ = __str__
