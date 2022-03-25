import logging

from .flumine import Flumine
from .simulation.simulation import FlumineSimulation
from .strategy.strategy import BaseStrategy
from .exceptions import FlumineException
from .__version__ import __title__, __version__, __author__

from betfairlightweight.resources import bettingresources
from .patching import EX, SP

# patch bflw with faster classes
bettingresources.RunnerBookEX = EX
bettingresources.RunnerBookSP = SP

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())
