import unittest
from unittest import mock

from flumine.markets.middleware import (
    Middleware,
    SimulatedMiddleware,
    RunnerAnalytics,
    OrderStatus,
)


class MiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.middleware = Middleware()

    def test_call(self):
        with self.assertRaises(NotImplementedError):
            self.middleware(None)


class SimulatedMiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.middleware = SimulatedMiddleware()

    def test_init(self):
        self.assertEqual(self.middleware.markets, {})

    @mock.patch(
        "flumine.markets.middleware.SimulatedMiddleware._process_simulated_orders"
    )
    @mock.patch("flumine.markets.middleware.SimulatedMiddleware._process_runner")
    def test_call(self, mock__process_runner, mock__process_simulated_orders):
        mock_market = mock.Mock(context={})
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.status = "ACTIVE"
        mock_market_book.runners = [mock_runner]
        mock_market.market_book = mock_market_book
        self.middleware(mock_market)
        mock__process_runner.assert_called_with({}, mock_runner)
        self.assertEqual(mock_market.context, {"simulated": {}})
        mock__process_simulated_orders.assert_called_with(mock_market, {})

    def test__process_simulated_orders(self):
        mock_market_book = mock.Mock()
        mock_order = mock.Mock()
        mock_order.status = OrderStatus.EXECUTABLE
        mock_market = mock.Mock()
        mock_order_two = mock.Mock()
        mock_order_two.status = OrderStatus.PENDING
        mock_order_three = mock.Mock()
        mock_order_three.status = OrderStatus.EXECUTABLE
        mock_order_three.simulated = False
        mock_market.blotter = [mock_order, mock_order_two, mock_order_three]
        mock_market_analytics = {(mock_order.selection_id, mock_order.handicap): "test"}
        mock_market.market_book = mock_market_book
        self.middleware._process_simulated_orders(mock_market, mock_market_analytics)
        mock_order.simulated.assert_called_with(mock_market_book, "test")
        mock_order_two.simulated.assert_not_called()

    @mock.patch("flumine.markets.middleware.RunnerAnalytics")
    def test__process_runner(self, mock_runner_analytics):
        market_analytics = {}
        mock_runner = mock.Mock()
        self.middleware._process_runner(market_analytics, mock_runner)
        self.assertEqual(len(market_analytics), 1)
        self.middleware._process_runner(market_analytics, mock_runner)
        self.assertEqual(len(market_analytics), 1)
        mock_runner_analytics.assert_called_with(mock_runner)


class RunnerAnalyticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_runner = mock.Mock()
        self.runner_analytics = RunnerAnalytics(self.mock_runner)

    def test_init(self):
        self.assertEqual(self.runner_analytics._runner, self.mock_runner)
        self.assertEqual(self.runner_analytics._traded_volume, [])
        self.assertEqual(self.runner_analytics.traded, {})

    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_traded")
    def test_call(self, mock__calculate_traded):
        mock_runner = mock.Mock()
        self.runner_analytics(mock_runner)
        mock__calculate_traded.assert_called_with(mock_runner)
        self.assertEqual(
            self.runner_analytics._traded_volume, mock_runner.ex.traded_volume
        )
        self.assertEqual(self.runner_analytics.traded, mock__calculate_traded())
        self.assertEqual(self.runner_analytics._runner, mock_runner)

    def test__calculate_traded_dict_empty(self):
        mock_runner = mock.Mock()
        mock_runner.ex.traded_volume = []
        self.assertEqual(self.runner_analytics._calculate_traded(mock_runner), {})

    def test__calculate_traded_dict_same(self):
        mock_runner = mock.Mock()
        mock_runner.ex.traded_volume = [{"price": 1.01, "size": 69}]
        self.runner_analytics._traded_volume = [{"price": 1.01, "size": 69}]
        self.assertEqual(self.runner_analytics._calculate_traded(mock_runner), {})

    def test__calculate_traded_dict_new(self):
        mock_runner = mock.Mock()
        mock_runner.ex.traded_volume = [{"price": 1.01, "size": 69}]
        self.runner_analytics._traded_volume = []
        self.assertEqual(
            self.runner_analytics._calculate_traded(mock_runner), {1.01: 69.0}
        )

    def test__calculate_traded_dict_new_multi(self):
        mock_runner = mock.Mock()
        mock_runner.ex.traded_volume = [
            {"price": 1.01, "size": 69},
            {"price": 10, "size": 32},
        ]
        self.runner_analytics._traded_volume = [{"price": 1.01, "size": 30}]
        self.assertEqual(
            self.runner_analytics._calculate_traded(mock_runner), {1.01: 39.0, 10: 32},
        )
