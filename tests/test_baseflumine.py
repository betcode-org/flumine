import unittest
from unittest import mock

from flumine.baseflumine import BaseFlumine


class BaseFlumineTest(unittest.TestCase):
    def setUp(self):
        self.mock_client = mock.Mock()
        self.base_flumine = BaseFlumine(self.mock_client)

    def test_init(self):
        self.assertFalse(self.base_flumine.BACKTEST)
        self.assertEqual(self.base_flumine.client, self.mock_client)
        self.assertFalse(self.base_flumine._running)
        self.assertEqual(self.base_flumine._logging_controls, [])
        self.assertEqual(self.base_flumine._trading_controls, [])
        self.assertEqual(self.base_flumine._workers, [])

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.base_flumine.run()

    def test_add_strategy(self):
        mock_strategy = mock.Mock()
        self.base_flumine.add_strategy(mock_strategy)
        self.assertEqual(len(self.base_flumine.strategies), 1)
        self.assertEqual(len(self.base_flumine.streams), 1)

    def test_add_worker(self):
        mock_worker = mock.Mock()
        self.base_flumine.add_worker(mock_worker)
        self.assertEqual(len(self.base_flumine._workers), 1)

    def test__add_default_workers(self):
        self.base_flumine._add_default_workers()
        self.assertEqual(len(self.base_flumine._workers), 0)

    def test__process_market_books(self):
        mock_event = mock.Mock()
        mock_market_book = mock.Mock()
        mock_event.event = [mock_market_book]
        self.base_flumine._process_market_books(mock_event)

    @mock.patch("flumine.baseflumine.Market")
    def test__add_live_market(self, mock_market):
        mock_market_book = mock.Mock()
        self.assertEqual(
            self.base_flumine._add_live_market("1.234", mock_market_book), mock_market()
        )
        self.assertEqual(len(self.base_flumine.markets._markets), 1)

    def test__process_raw_data(self):
        mock_event = mock.Mock()
        mock_event.event = (12, 12345, {})
        self.base_flumine._process_raw_data(mock_event)

    def test__process_end_flumine(self):
        self.base_flumine._process_end_flumine()

    def test_status(self):
        self.base_flumine._running = True
        self.assertEqual(self.base_flumine.status, "running")
        self.base_flumine._running = False
        self.assertEqual(self.base_flumine.status, "not running")

    def test_enter_exit(self):
        with self.base_flumine:
            self.assertTrue(self.base_flumine._running)
            self.mock_client.login.assert_called_with()

        self.assertFalse(self.base_flumine._running)
        self.mock_client.logout.assert_called_with()
