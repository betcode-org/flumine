class FlumineException(Exception):
    """Base class for Flumine Errors"""

    pass


class RunError(FlumineException):
    """Exception raised if error
    in `Flumine.run()``
    """

    def __init__(self, message):
        super(RunError, self).__init__(message)


class ListenerError(FlumineException):
    """Error raised if error in Listener"""

    def __int__(self, message):
        super(ListenerError, self).__init__(message)


class OrderError(FlumineException):
    """Exception raised if incorrect
    order/order_type requested.
    """

    def __init__(self, message):
        super(OrderError, self).__init__(message)


class OrderUpdateError(FlumineException):
    """Exception raised if order update
    incorrect.
    """

    def __init__(self, message):
        super(OrderUpdateError, self).__init__(message)


class OrderExecutionError(FlumineException):
    """Exception raised error in package during
    execution.
    """

    pass


class ControlError(FlumineException):
    """Exception raised if order voilates
    a control.
    """

    def __init__(self, message):
        super(ControlError, self).__init__(message)


class ClientError(FlumineException):
    """Exception raised on client
    error.
    """

    def __init__(self, message):
        super(ClientError, self).__init__(message)
