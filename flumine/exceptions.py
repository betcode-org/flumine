

class FlumineException(Exception):
    """Base class for Flumine Errors"""
    pass


class RunError(FlumineException):
    """Error raised if start() called when already running"""

    def __init__(self):
        message = 'Flumine is already running'
        super(RunError, self).__init__(message)
