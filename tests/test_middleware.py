import unittest
from unittest import mock

from flumine.markets.middleware import Middleware, SimulatedMiddleware, RunnerAnalytics


class MiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.middleware = Middleware()

    def test_call(self):
        with self.assertRaises(NotImplementedError):
            self.middleware(None, None)


class SimulatedMiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.middleware = SimulatedMiddleware()

    def test_init(self):
        self.assertEqual(self.middleware.runners, {})

    @mock.patch("flumine.markets.middleware.SimulatedMiddleware._process_runner")
    def test_call(self, mock__process_runner):
        mock_market_catalogue = mock.Mock()
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.status = "ACTIVE"
        mock_market_book.runners = [mock_runner]
        self.middleware(mock_market_catalogue, mock_market_book)
        mock__process_runner.assert_called_with(mock_runner)

    @mock.patch("flumine.markets.middleware.RunnerAnalytics")
    def test__process_runner(self, mock_runner_analytics):
        mock_runner = mock.Mock()
        self.middleware._process_runner(mock_runner)
        self.assertEqual(len(self.middleware.runners), 1)
        self.middleware._process_runner(mock_runner)
        self.assertEqual(len(self.middleware.runners), 1)
        mock_runner_analytics.assert_called_with(mock_runner)


class RunnerAnalyticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_runner = mock.Mock()
        self.runner_analytics = RunnerAnalytics(self.mock_runner)

    def test_init(self):
        self.assertEqual(self.runner_analytics._runner, self.mock_runner)
        self.assertEqual(self.runner_analytics._volume_dict, [])
        self.assertEqual(self.runner_analytics.traded_dictionary, {})

    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_traded_dict")
    def test_call(self, mock__calculate_traded_dict):
        mock_runner = mock.Mock()
        self.runner_analytics(mock_runner)
        mock__calculate_traded_dict.assert_called_with(mock_runner)
        self.assertEqual(
            self.runner_analytics._volume_dict, mock_runner.ex.traded_volume
        )
        self.assertEqual(
            self.runner_analytics.traded_dictionary, mock__calculate_traded_dict()
        )

    def test__calculate_traded_dict_empty(self):
        mock_runner = mock.Mock()
        mock_runner.ex.traded_volume = []
        self.assertEqual(self.runner_analytics._calculate_traded_dict(mock_runner), {})

    def test__calculate_traded_dict_same(self):
        mock_runner = mock.Mock()
        mock_runner.ex.traded_volume = [{"price": 1.01, "size": 69}]
        self.runner_analytics._volume_dict = [{"price": 1.01, "size": 69}]
        self.assertEqual(self.runner_analytics._calculate_traded_dict(mock_runner), {})

    def test__calculate_traded_dict_new(self):
        mock_runner = mock.Mock()
        mock_runner.ex.traded_volume = [{"price": 1.01, "size": 69}]
        self.runner_analytics._volume_dict = []
        self.assertEqual(
            self.runner_analytics._calculate_traded_dict(mock_runner), {1.01: 69.0}
        )

    def test__calculate_traded_dict_new_multi(self):
        mock_runner = mock.Mock()
        mock_runner.ex.traded_volume = [
            {"price": 1.01, "size": 69},
            {"price": 10, "size": 32},
        ]
        self.runner_analytics._volume_dict = [{"price": 1.01, "size": 30}]
        self.assertEqual(
            self.runner_analytics._calculate_traded_dict(mock_runner),
            {1.01: 39.0, 10: 32},
        )
