import unittest
from unittest import mock

from flumine.flumine import Flumine
from flumine.exceptions import RunError
from betfairlightweight import BetfairError


class FlumineTest(unittest.TestCase):
    def setUp(self):
        self.mock_trading = mock.Mock()
        self.flumine = Flumine(self.mock_trading)

    def test_run(self):
        pass

    def test_str(self):
        assert str(self.flumine) == "<Flumine [not running]>"

    def test_repr(self):
        assert repr(self.flumine) == "<Flumine>"
