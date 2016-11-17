import unittest
from unittest import mock

from flumine.flumine import Flumine


class FlumineTest(unittest.TestCase):

    def setUp(self):
        self.trading = mock.Mock()
        self.strategies = mock.Mock()
        self.flumine = Flumine(self.trading, self.strategies)

    def test_init(self):
        assert self.flumine.trading == self.trading
        assert self.flumine.strategies == self.strategies

    def test_str(self):
        assert str(self.flumine) == '<Flumine>'
