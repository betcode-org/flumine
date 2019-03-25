import logging

from .flumine import Flumine
from . import resources
from .exceptions import FlumineException


__title__ = 'flumine'
__version__ = '0.7.0'
__author__ = 'Liam Pauling'


# Set default logging handler to avoid "No handler found" warnings.
class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logging.getLogger(__name__).addHandler(NullHandler())
