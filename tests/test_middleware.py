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
    LIVE_STATUS,
    SimulatedSportsDataMiddleware,
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
        self.assertEqual(
            LIVE_STATUS,
            [
                OrderStatus.EXECUTABLE,
                OrderStatus.CANCELLING,
                OrderStatus.UPDATING,
                OrderStatus.REPLACING,
            ],
        )

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
        mock__process_runner.assert_called_with({}, mock_runner)
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
        # defined in the example here: https://github.com/betcode-org/flumine/issues/454
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
        # defined in the example here: https://github.com/betcode-org/flumine/issues/454
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

    def test__calculate_reduction_factor(self):
        self.assertEqual(self.middleware._calculate_reduction_factor(10, 10), 9)
        self.assertEqual(self.middleware._calculate_reduction_factor(1000, 0), 1000)
        self.assertEqual(self.middleware._calculate_reduction_factor(1000, 5), 950)
        self.assertEqual(self.middleware._calculate_reduction_factor(3.2, 75.18), 1.01)
        self.assertEqual(self.middleware._calculate_reduction_factor(10, 75.18), 2.48)
        self.assertEqual(self.middleware._calculate_reduction_factor(1.01, 75.18), 1.01)

    @mock.patch("flumine.markets.middleware.config")
    def test__process_simulated_orders_strategy_isolation(self, mock_config):
        mock_config.simulated_strategy_isolation = True
        mock_market_book = mock.Mock()
        mock_market = mock.Mock()
        mock_order = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.EXECUTABLE, side="LAY"
        )
        mock_order.order_type.price = 1.02
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order_two = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.PENDING
        )
        mock_order_three = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.EXECUTABLE, simulated=False
        )
        mock_market.blotter._strategy_orders = {
            "test": [mock_order, mock_order_two, mock_order_three]
        }
        mock_market_analytics = {
            (mock_order.selection_id, mock_order.handicap): mock.Mock(traded={1: 2})
        }
        mock_market.market_book = mock_market_book
        self.middleware._process_simulated_orders(mock_market, mock_market_analytics)
        mock_order.simulated.assert_called_with(mock_market_book, {1: 2})
        mock_order_two.simulated.assert_not_called()

    @mock.patch("flumine.markets.middleware.config")
    def test__process_simulated_orders(self, mock_config):
        mock_config.simulated_strategy_isolation = False
        mock_market_book = mock.Mock()
        mock_market = mock.Mock()
        mock_order = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.EXECUTABLE, side="LAY"
        )
        mock_order.order_type.price = 1.02
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order_two = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.PENDING
        )
        mock_order_three = mock.Mock(
            selection_id=123, handicap=1, status=OrderStatus.EXECUTABLE, simulated=False
        )
        mock_market.blotter.live_orders = [
            mock_order,
            mock_order_two,
            mock_order_three,
        ]
        mock_market_analytics = {
            (mock_order.selection_id, mock_order.handicap): mock.Mock(traded={1: 2})
        }
        mock_market.market_book = mock_market_book
        self.middleware._process_simulated_orders(mock_market, mock_market_analytics)
        mock_order.simulated.assert_called_with(mock_market_book, {1: 2})
        mock_order_two.simulated.assert_not_called()

    def test__sort_orders(self):
        order_one = mock.Mock(side="LAY", bet_id=1)
        order_one.order_type.price = 1.01
        order_two = mock.Mock(side="LAY", bet_id=2)
        order_two.order_type.price = 1.02
        order_three = mock.Mock(side="LAY", bet_id=3)
        order_three.order_type.price = 1.01
        order_four = mock.Mock(side="BACK", bet_id=4)
        order_four.order_type.price = 1.2
        order_five = mock.Mock(side="BACK", bet_id=5)
        order_five.order_type.price = 1.2
        order_six = mock.Mock(side="BACK", bet_id=6)
        order_six.order_type.price = 1.19
        order_seven = mock.Mock(side="BACK", bet_id=6)
        order_seven.order_type.price = "ERROR"
        order_seven.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        orders = [
            order_one,
            order_two,
            order_three,
            order_four,
            order_five,
            order_six,
            order_seven,
        ]
        self.assertEqual(
            self.middleware._sort_orders(orders),
            [
                order_two,
                order_one,
                order_three,
                order_six,
                order_four,
                order_five,
                order_seven,
            ],
        )

    @mock.patch("flumine.markets.middleware.RunnerAnalytics")
    def test__process_runner(self, mock_runner_analytics):
        market_analytics = {}
        mock_runner = mock.Mock()
        self.middleware._process_runner(market_analytics, mock_runner)
        self.assertEqual(len(market_analytics), 1)
        self.middleware._process_runner(market_analytics, mock_runner)
        self.assertEqual(len(market_analytics), 1)
        mock_runner_analytics.assert_called_with(mock_runner)
        mock_runner_analytics().assert_called_with(mock_runner)


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
        self.assertEqual(self.runner_analytics._p_v, {1.01: 2})

    @mock.patch("flumine.markets.middleware.RunnerAnalytics._calculate_traded")
    def test_call(self, mock__calculate_traded):
        mock_runner = mock.Mock()
        self.runner_analytics(mock_runner)
        mock__calculate_traded.assert_called_with(mock_runner.ex.traded_volume)
        self.assertEqual(
            self.runner_analytics._traded_volume, mock_runner.ex.traded_volume
        )
        self.assertEqual(self.runner_analytics.traded, mock__calculate_traded())
        self.assertEqual(self.runner_analytics._runner, mock_runner)

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


class SimulatedSportsDataMiddlewareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.middleware = SimulatedSportsDataMiddleware("cricketSubscription", "test")

    def test_init(self):
        self.assertEqual(self.middleware.operation, "cricketSubscription")
        self.assertEqual(self.middleware.directory, "test")
        self.assertIsNone(self.middleware._gen)
        self.assertIsNone(self.middleware._next)

    @mock.patch(
        "flumine.markets.middleware.call_strategy_error_handling", return_value=True
    )
    def test_call(self, mock_call_strategy_error_handling):
        mock_gen = mock.Mock()
        mock_update_one = mock.Mock(publish_time_epoch=121, market_id="1.1")
        mock_update_two = mock.Mock(publish_time_epoch=122, market_id="1.1")
        mock_update_three = mock.Mock(publish_time_epoch=123, market_id="1.1")
        mock_update_four = mock.Mock(publish_time_epoch=121, market_id="1.2")
        mock_gen.__next__ = mock.Mock(
            side_effect=[[mock_update_four], [mock_update_two], [mock_update_three]]
        )
        self.middleware._gen = mock_gen
        self.middleware._next = [mock_update_one]
        mock_strategy = mock.Mock(stream_ids=[456])
        mock_market = mock.Mock(market_id="1.1")
        mock_market.market_book.publish_time_epoch = 123
        mock_market.market_book.streaming_unique_id = 456
        mock_market.flumine.strategies = [mock_strategy]
        self.middleware(mock_market)
        mock_call_strategy_error_handling.call_count = 2
        mock_call_strategy_error_handling.assert_has_calls(
            [
                mock.call(
                    mock_strategy.check_sports_data, mock_market, mock_update_one
                ),
                mock.call(
                    mock_strategy.process_sports_data, mock_market, mock_update_one
                ),
                mock.call(
                    mock_strategy.check_sports_data, mock_market, mock_update_two
                ),
                mock.call(
                    mock_strategy.process_sports_data, mock_market, mock_update_two
                ),
            ]
        )

    @mock.patch(
        "flumine.markets.middleware.SimulatedSportsDataMiddleware._create_generator"
    )
    def test_add_market(self, mock__create_generator):
        mock_market = mock.Mock(market_id="marketId")
        self.assertIsNone(self.middleware.add_market(mock_market))
        mock__create_generator.assert_called_with(
            "test/marketId", "cricketSubscription", 123
        )
        self.assertEqual(self.middleware._gen, mock__create_generator()())
        self.assertEqual(self.middleware._next, next(mock__create_generator()()))

    def test_remove_market(self):
        self.middleware.remove_market(mock.Mock())
        self.assertIsNone(self.middleware._gen)
        self.assertIsNone(self.middleware._next)

    @mock.patch("flumine.markets.middleware.FlumineHistoricalGeneratorStream")
    @mock.patch("flumine.markets.middleware.HistoricListener")
    def test__create_generator(self, mock_listener, mock_stream):
        gen = self.middleware._create_generator(
            "test/marketId", "cricketSubscription", 123
        )
        mock_listener.assert_called_with(max_latency=None, update_clk=False)
        mock_stream.assert_called_with(
            file_path="test/marketId",
            listener=mock_listener(),
            operation="cricketSubscription",
            unique_id=123,
        )
        self.assertEqual(gen, mock_stream().get_generator())
