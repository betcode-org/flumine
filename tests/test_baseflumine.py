import unittest
from unittest import mock

from flumine.baseflumine import BaseFlumine
from flumine.exceptions import RunError
from betfairlightweight import BetfairError


class BaseFlumineTest(unittest.TestCase):
    def setUp(self):
        self.mock_trading = mock.Mock()
        self.base_flumine = BaseFlumine(self.mock_trading)

    def test_init(self):
        self.assertEqual(self.base_flumine.trading, self.mock_trading)
        self.assertFalse(self.base_flumine._running)
        self.assertEqual(self.base_flumine._logging_controls, [])
        self.assertEqual(self.base_flumine._trading_controls, [])

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.base_flumine.run()

    def test_status(self):
        self.base_flumine._running = True
        self.assertEqual(self.base_flumine.status, "running")
        self.base_flumine._running = False
        self.assertEqual(self.base_flumine.status, "not running")

    def test_enter_exit(self):
        with self.base_flumine:
            self.assertTrue(self.base_flumine._running)
            self.mock_trading.login.assert_called()

        self.assertFalse(self.base_flumine._running)
        self.mock_trading.logout.assert_called()
