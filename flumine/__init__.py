import logging

from .flumine import Flumine
from .backtest.backtest import FlumineBacktest
from .strategy.strategy import BaseStrategy
from .exceptions import FlumineException
from .__version__ import __title__, __version__, __author__

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())
