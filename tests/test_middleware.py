import unittest
from unittest import mock

from flumine.markets.middleware import (
    Middleware,
    SimulatedMiddleware,
    RunnerAnalytics,
    OrderStatus,
    OrderTypes,
    WIN_MINIMUM_ADJUSTMENT_FACTOR,
    PLACE_MINIMUM_ADJUSTMENT_FACTOR,
)
from flumine.order.ordertype import MarketOnCloseOrder


class MiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.middleware = Middleware()

    def test_call(self):
        self.middleware(None)

    def test_add_market(self):
        mock_market = mock.Mock()
        self.assertIsNone(self.middleware.add_market(mock_market))

    def test_remove_market(self):
        mock_market = mock.Mock()
        self.assertIsNone(self.middleware.remove_market(mock_market))


class SimulatedMiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.middleware = SimulatedMiddleware()

    def test_init(self):
        self.assertEqual(self.middleware.markets, {})
        self.assertEqual(self.middleware._runner_removals, [])
        self.assertEqual(WIN_MINIMUM_ADJUSTMENT_FACTOR, 2.5)
        self.assertEqual(PLACE_MINIMUM_ADJUSTMENT_FACTOR, 0)

    @mock.patch(
        "flumine.markets.middleware.SimulatedMiddleware._process_simulated_orders"
    )
    @mock.patch("flumine.markets.middleware.SimulatedMiddleware._process_runner")
    def test_call(self, mock__process_runner, mock__process_simulated_orders):
        mock_market = mock.Mock(context={})
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock(status="ACTIVE")
        mock_market_book.runners = [mock_runner]
        mock_market.market_book = mock_market_book
        self.middleware(mock_market)
        mock__process_runner.assert_called_with({}, mock_runner, True)
        self.assertEqual(mock_market.context, {"simulated": {}})
        mock__process_simulated_orders.assert_called_with(mock_market, {})

    @mock.patch(
        "flumine.markets.middleware.SimulatedMiddleware._process_simulated_orders"
    )
    @mock.patch(
        "flumine.markets.middleware.SimulatedMiddleware._process_runner_removal"
    )
    def test_call_non_runner(
        self, mock__process_runner_removal, mock__process_simulated_orders
    ):
        mock_market = mock.Mock(context={})
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock(status="REMOVED")
        mock_market_book.runners = [mock_runner]
        mock_market.market_book = mock_market_book
        self.middleware(mock_market)
        self.assertEqual(
            self.middleware._runner_removals,
            [
                (
                    mock_runner.selection_id,
                    mock_runner.handicap,
                    mock_runner.adjustment_factor,
                )
            ],
        )
        mock__process_runner_removal.assert_called_with(
            mock_market,
            mock_runner.selection_id,
            mock_runner.handicap,
            mock_runner.adjustment_factor,
        )

    def test_remove_market(self):
        mock_market = mock.Mock(market_id="1.23")
        self.middleware.markets = {mock_market.market_id: []}
        self.middleware.remove_market(mock_market)
        self.middleware.remove_market(mock_market)
        self.assertEqual(self.middleware.markets, {})

    def test__process_runner_removal(self):
        mock_simulated = mock.MagicMock(matched=[[123, 8.6, 10]])
        mock_simulated.__bool__.return_value = True
        mock_order = mock.Mock(simulated=mock_simulated, info={})
        mock_simulated_two = mock.MagicMock(matched=[[123, 8.6, 10]])
        mock_simulated_two.__bool__.return_value = False
        mock_order_two = mock.Mock(simulated=mock_simulated_two, info={})
        mock_market = mock.Mock(blotter=[mock_order, mock_order_two])
        self.middleware._process_runner_removal(mock_market, 12345, 0, 16.2)
        self.assertEqual(mock_order.simulated.matched, [[123, 7.21, 10]])
        self.assertEqual(mock_order.simulated.average_price_matched, 7.21)
        self.assertEqual(mock_order_two.simulated.matched, [[123, 8.6, 10]])

    def test__process_runner_removal_under_limit(self):
        mock_simulated = mock.MagicMock(matched=[[123, 8.6, 10]])
        mock_simulated.__bool__.return_value = True
        mock_order = mock.Mock(simulated=mock_simulated)
        mock_market = mock.Mock(blotter=[mock_order])
        self.middleware._process_runner_removal(mock_market, 12345, 0, 2.4)
        self.assertEqual(mock_order.simulated.matched, [[123, 8.6, 10]])

    def test__process_runner_removal_void(self):
        mock_simulated = mock.MagicMock(matched=[[123, 8.6, 10]])
        mock_simulated.__bool__.return_value = True
        mock_order = mock.Mock(
            lookup=("1.23", 12345, 0), simulated=mock_simulated, info={}
        )
        mock_order.order_type.size = 10
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_market = mock.Mock(market_id="1.23", blotter=[mock_order])
        self.middleware._process_runner_removal(mock_market, 12345, 0, 16.2)
        self.assertEqual(mock_order.simulated.size_matched, 0)
        self.assertEqual(mock_order.simulated.average_price_matched, 0)
        self.assertEqual(mock_order.simulated.matched, [])
        self.assertEqual(mock_order.simulated.size_voided, 10)

    def test__process_runner_removal_none(self):
        mock_simulated = mock.MagicMock(matched=[[123, 8.6, 10]])
        mock_simulated.__bool__.return_value = True
        mock_order = mock.Mock(simulated=mock_simulated)
        mock_market = mock.Mock(blotter=[mock_order])
        self.middleware._process_runner_removal(mock_market, 12345, 0, None)
        self.assertEqual(mock_order.simulated.matched, [[123, 8.6, 10]])

    def test__process_runner_removal_sp_win(self):
        order_type = MarketOnCloseOrder(liability=200)
        mock_order = mock.Mock(
            selection_id=1234,
            handicap=0,
            order_type=order_type,
            info={},
            side="LAY",
            current_order=mock.Mock(size_matched=0),
            average_price_matched=None,
        )

        mock_market_book = mock.Mock()
        mock_market_book.runners = [
            mock.Mock(selection_id=1234, handicap=0, adjustment_factor=20)
        ]
        mock_market = mock.Mock(
            market_type="WIN", blotter=[mock_order], market_book=mock_market_book
        )
        self.middleware._process_runner_removal(mock_market, 12345, 0, 50)

        # The liability of £200 is adjusted by the multiplier of 37.5%, which s
        # defined in the example here: https://github.com/liampauling/flumine/issues/454
        self.assertEqual(mock_order.order_type.liability, 75)

    def test__process_runner_removal_sp_win_inplay(self):
        order_type = MarketOnCloseOrder(liability=200)
        mock_order = mock.Mock(
            selection_id=1234,
            handicap=0,
            order_type=order_type,
            info={},
            side="LAY",
            current_order=mock.Mock(size_matched=0),
            average_price_matched=10,
        )

        mock_market_book = mock.Mock()
        mock_market_book.runners = [
            mock.Mock(selection_id=1234, handicap=0, adjustment_factor=20)
        ]
        mock_market = mock.Mock(
            market_type="WIN", blotter=[mock_order], market_book=mock_market_book
        )
        self.middleware._process_runner_removal(mock_market, 12345, 0, 50)

        # The liability of £200 is adjusted by the multiplier of 37.5%, which s
        # defined in the example here: https://github.com/liampauling/flumine/issues/454
        self.assertEqual(mock_order.order_type.liability, 75)
        # Size matched should be 75 / (10.0-1.0) \approx 8.33
        self.assertEqual(8.33, mock_order.current_order.size_matched)

    def test__process_runner_removal_sp_place(self):
        order_type = MarketOnCloseOrder(liability=200)
        mock_order = mock.Mock(
            selection_id=1234,
            handicap=0,
            order_type=order_type,
            info={},
            side="LAY",
            current_order=mock.Mock(size_matched=0),
            average_price_matched=None,
        )

        mock_market_book = mock.Mock()
        mock_market_book.runners = [
            mock.Mock(selection_id=1234, handicap=0, adjustment_factor=20)
        ]
        mock_market = mock.Mock(
            market_type="PLACE", blotter=[mock_order], market_book=mock_market_book
        )
        self.middleware._process_runner_removal(mock_market, 12345, 0, 50)

        # The liability of £200 is reduced by the non runner's adjustment factor of 50%
        self.assertEqual(mock_order.order_type.liability, 100)

    def test__process_runner_removal_sp_place_inplay(self):
        order_type = MarketOnCloseOrder(liability=200)
        mock_order = mock.Mock(
            selection_id=1234,
            handicap=0,
            order_type=order_type,
            info={},
            side="LAY",
            current_order=mock.Mock(size_matched=0),
            average_price_matched=10.0,
        )

        mock_market_book = mock.Mock()
        mock_market_book.runners = [
            mock.Mock(selection_id=1234, handicap=0, adjustment_factor=20)
        ]
        mock_market = mock.Mock(
            market_type="PLACE", blotter=[mock_order], market_book=mock_market_book
        )
        self.middleware._process_runner_removal(mock_market, 12345, 0, 50)

        # The liability of £200 is reduced by the non runner's adjustment factor of 50%
        self.assertEqual(mock_order.order_type.liability, 100)
        # Size matched should be 100 / (10.0-1.0) \approx 11.11
        self.assertEqual(11.11, mock_order.current_order.size_matched)

    def test__process_streaming_update(self):
        mock_market_book = mock.Mock(
            streaming_update={"img": True, "rc": [{"id": 3}, {"id": 4}]},
            runners=[mock.Mock(selection_id=1), mock.Mock(selection_id=2)],
        )
        self.assertEqual(
            self.middleware._process_streaming_update(mock_market_book), [1, 2]
        )
        mock_market_book = mock.Mock(
            streaming_update={"marketDefinition": {1: 2}, "rc": [{"id": 3}, {"id": 4}]},
            runners=[mock.Mock(selection_id=1), mock.Mock(selection_id=2)],
        )
        self.assertEqual(
            self.middleware._process_streaming_update(mock_market_book), [1, 2]
        )
        mock_market_book = mock.Mock(
            streaming_update={"rc": [{"id": 3}, {"id": 4}]},
            runners=[mock.Mock(selection_id=1), mock.Mock(selection_id=2)],
        )
        self.assertEqual(
            self.middleware._process_streaming_update(mock_market_book), [3, 4]
        )

    def test__calculate_reduction_factor(self):
        self.assertEqual(self.middleware._calculate_reduction_factor(10, 10), 9)
        self.assertEqual(self.middleware._calculate_reduction_factor(1000, 0), 1000)
        self.assertEqual(self.middleware._calculate_reduction_factor(1000, 5), 950)
        self.assertEqual(self.middleware._calculate_reduction_factor(3.2, 75.18), 1.01)
        self.assertEqual(self.middleware._calculate_reduction_factor(10, 75.18), 2.48)
        self.assertEqual(self.middleware._calculate_reduction_factor(1.01, 75.18), 1.01)

    def test__process_simulated_orders(self):
        mock_market_book = mock.Mock()
        mock_market = mock.Mock()
        mock_order = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.EXECUTABLE
        )
        mock_order_two = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.PENDING
        )
        mock_order_three = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.EXECUTABLE, simulated=False
        )
        mock_market.blotter._live_orders = [
            mock_order,
            mock_order_two,
            mock_order_three,
        ]
        mock_market_analytics = {(mock_order.selection_id, mock_order.handicap): "test"}
        mock_market.market_book = mock_market_book
        self.middleware._process_simulated_orders(mock_market, mock_market_analytics)
        mock_order.simulated.assert_called_with(mock_market_book, "test")
        mock_order_two.simulated.assert_not_called()

    @mock.patch("flumine.markets.middleware.RunnerAnalytics")
    def test__process_runner(self, mock_runner_analytics):
        market_analytics = {}
        mock_runner = mock.Mock()
        self.middleware._process_runner(market_analytics, mock_runner, True)
        self.assertEqual(len(market_analytics), 1)
        self.middleware._process_runner(market_analytics, mock_runner, False)
        self.assertEqual(len(market_analytics), 1)
        mock_runner_analytics.assert_called_with(mock_runner)
        mock_runner_analytics().assert_called_with(mock_runner, False)


class RunnerAnalyticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_runner = mock.Mock()
        self.mock_runner.ex.traded_volume = [{"price": 1.01, "size": 2}]
        self.runner_analytics = RunnerAnalytics(self.mock_runner)

    def test_init(self):
        self.assertEqual(self.runner_analytics._runner, self.mock_runner)
        self.assertEqual(
            self.runner_analytics._traded_volume, self.mock_runner.ex.traded_volume
        )
        self.assertEqual(self.runner_analytics.traded, {})
        self.assertEqual(self.runner_analytics.matched, 0)
        self.assertIsNone(self.runner_analytics.middle)
        self.assertEqual(self.runner_analytics._p_v, {1.01: 2})

    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_matched")
    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_middle")
    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_traded")
    def test_call(
        self, mock__calculate_traded, mock__calculate_middle, mock__calculate_matched
    ):
        mock_runner = mock.Mock()
        self.runner_analytics(mock_runner, True)
        mock__calculate_traded.assert_called_with(mock_runner.ex.traded_volume)
        mock__calculate_middle.assert_called_with(self.mock_runner)
        mock__calculate_matched.assert_called_with(mock_runner)
        self.assertEqual(
            self.runner_analytics._traded_volume, mock_runner.ex.traded_volume
        )
        self.assertEqual(self.runner_analytics.middle, mock__calculate_middle())
        self.assertEqual(self.runner_analytics.matched, mock__calculate_matched())
        self.assertEqual(self.runner_analytics.traded, mock__calculate_traded())
        self.assertEqual(self.runner_analytics._runner, mock_runner)

    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_matched")
    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_middle")
    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_traded")
    def test_call_no_update(
        self, mock__calculate_traded, mock__calculate_middle, mock__calculate_matched
    ):
        mock_runner = mock.Mock()
        self.runner_analytics(mock_runner, False)
        mock__calculate_traded.assert_not_called()
        mock__calculate_middle.assert_not_called()
        mock__calculate_matched.assert_not_called()
        self.assertEqual(self.runner_analytics.matched, 0)
        self.assertEqual(self.runner_analytics.traded, {})

    def test__calculate_traded_dict_empty(self):
        self.runner_analytics._traded_volume = []
        self.assertEqual(self.runner_analytics._calculate_traded([]), {})

    def test__calculate_traded_dict_same(self):
        traded_volume = [{"price": 1.01, "size": 69}]
        self.runner_analytics._traded_volume = [{"price": 1.01, "size": 69}]
        self.runner_analytics._p_v = {1.01: 69}
        self.assertEqual(self.runner_analytics._calculate_traded(traded_volume), {})
        self.assertEqual(self.runner_analytics._p_v, {1.01: 69})

    def test__calculate_traded_dict_new(self):
        traded_volume = [{"price": 1.01, "size": 69}]
        self.runner_analytics._traded_volume = []
        self.assertEqual(
            self.runner_analytics._calculate_traded(traded_volume), {1.01: 67.0}
        )
        self.assertEqual(self.runner_analytics._p_v, {1.01: 69})

    def test__calculate_traded_dict_new_multi(self):
        traded_volume = [
            {"price": 1.01, "size": 69},
            {"price": 10, "size": 32},
        ]
        self.runner_analytics._traded_volume = [{"price": 1.01, "size": 30}]
        self.runner_analytics._p_v = {1.01: 30}
        self.assertEqual(
            self.runner_analytics._calculate_traded(traded_volume),
            {1.01: 39.0, 10: 32},
        )
        self.assertEqual(self.runner_analytics._p_v, {1.01: 69, 10: 32})

    def test__calculate_middle(self):
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = []
        mock_runner.ex.available_to_lay = []
        self.assertEqual(self.runner_analytics._calculate_middle(mock_runner), 500.5)
        mock_runner.ex.available_to_back = [{"price": 2.00}]
        mock_runner.ex.available_to_lay = [{"price": 2.02}]
        self.assertEqual(self.runner_analytics._calculate_middle(mock_runner), 2.01)
        mock_runner.ex.available_to_back = [{"price": 10.00}]
        mock_runner.ex.available_to_lay = [{"price": 15.5}]
        self.assertEqual(self.runner_analytics._calculate_middle(mock_runner), 12.75)

    def test__calculate_matched(self):
        self.runner_analytics._runner.total_matched = 12344
        mock_runner = mock.Mock(total_matched=12345)
        self.assertEqual(self.runner_analytics._calculate_matched(mock_runner), 1)
        self.runner_analytics._runner = mock_runner
        self.assertEqual(self.runner_analytics._calculate_matched(mock_runner), 0)

    def test__calculate_matched_runner_removal(self):
        self.runner_analytics._runner.total_matched = 12344
        mock_runner = mock.Mock(total_matched=0)
        self.assertEqual(self.runner_analytics._calculate_matched(mock_runner), 0)
        self.runner_analytics._runner = mock_runner
        self.assertEqual(self.runner_analytics._calculate_matched(mock_runner), 0)
