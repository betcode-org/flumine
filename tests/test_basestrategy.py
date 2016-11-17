import unittest

from flumine.strategies.basestrategy import BaseStrategy


class BaseEndPointTest(unittest.TestCase):

    def setUp(self):
        self.base_strategy = BaseStrategy()

    def test_str(self):
        assert str(self.base_strategy) == '<BASE_STRATEGY>'
