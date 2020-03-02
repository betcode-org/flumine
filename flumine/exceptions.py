class FlumineException(Exception):
    """Base class for Flumine Errors"""

    pass


class ListenerError(FlumineException):
    """Error raised if error in Listener"""

    def __int__(self, message):
        super(ListenerError, self).__init__(message)
