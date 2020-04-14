class FlumineException(Exception):
    """Base class for Flumine Errors"""

    pass


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
