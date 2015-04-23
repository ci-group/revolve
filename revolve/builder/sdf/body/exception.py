class ArityException(BaseException):
    def __init__(self, *args, **kwargs):
        super(ArityException, self).__init__(self, *args, **kwargs)