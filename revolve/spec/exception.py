class RobotSpecificationException(BaseException):
    def __init__(self, msg):
        super(RobotSpecificationException, self).__init__(msg)


def err(msg):
    """
    Simple internal error function
    :param msg:
    :return:
    """
    raise RobotSpecificationException("Error: %s" % msg)