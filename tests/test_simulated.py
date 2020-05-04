import unittest
from unittest import mock

from flumine.backtest import simulated


class SimulatedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.simulated = simulated.Simulated()

    def test_init(self):
        self.assertEqual(self.simulated, self.simulated)
