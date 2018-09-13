

class FlumineException(Exception):
    """Base class for Flumine Errors"""
    pass


class RunError(FlumineException):
    """Error raised if start() called when already running"""

    def __init__(self, message):
        super(RunError, self).__init__(message)


class ListenerError(FlumineException):
    """Error raised if error in Listener"""

    def __int__(self, message):
        super(ListenerError, self).__init__(message)


class StreamError(FlumineException):
    """Error raise if invalid stream_type provided"""

    def __int__(self, message):
        super(StreamError, self).__init__(message)
