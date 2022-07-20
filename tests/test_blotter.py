import unittest
from unittest import mock

from flumine.markets.blotter import Blotter, PENDING_STATUS
from flumine.order.order import OrderStatus
from flumine.order.ordertype import MarketOnCloseOrder, LimitOrder, LimitOnCloseOrder


class BlotterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.blotter = Blotter("1.23")

    def test_init(self):
        self.assertEqual(self.blotter.market_id, "1.23")
        self.assertFalse(self.blotter.active)
        self.assertEqual(self.blotter._orders, {})
        self.assertEqual(self.blotter._bet_id_lookup, {})
        self.assertEqual(self.blotter._live_orders, [])
        self.assertEqual(self.blotter._trades, {})
        self.assertEqual(self.blotter._strategy_orders, {})
        self.assertEqual(self.blotter._strategy_selection_orders, {})
        self.assertEqual(self.blotter._client_orders, {})
        self.assertEqual(self.blotter._client_strategy_orders, {})
        self.assertEqual(
            PENDING_STATUS,
            [
                OrderStatus.PENDING,
                OrderStatus.VIOLATION,
                OrderStatus.EXPIRED,
            ],
        )

    def test_get_order_bet_id(self):
        self.assertIsNone(self.blotter.get_order_bet_id("123"))
        mock_order = mock.Mock(selection_id=2, handicap=3, bet_id="123")
        self.blotter["456"] = mock_order
        self.assertEqual(self.blotter.get_order_bet_id("123"), mock_order)

    def test_strategy_orders(self):
        mock_order_one = mock.Mock(
            selection_id=2, handicap=3, status=OrderStatus.EXECUTABLE, size_matched=1
        )
        mock_order_one.trade.strategy = 69
        self.blotter["12345"] = mock_order_one
        mock_order_two = mock.Mock(
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTION_COMPLETE,
            size_matched=0,
        )
        mock_order_two.trade.strategy = 69
        self.blotter["12345"] = mock_order_two
        mock_order_three = mock.Mock(
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTION_COMPLETE,
            size_matched=1,
        )
        mock_order_three.trade.strategy = 69
        self.blotter["12345"] = mock_order_three
        self.assertEqual(self.blotter.strategy_orders(12), [])
        self.assertEqual(
            self.blotter.strategy_orders(69),
            [mock_order_one, mock_order_two, mock_order_three],
        )
        self.assertEqual(
            self.blotter.strategy_orders(
                69, order_status=[OrderStatus.EXECUTION_COMPLETE]
            ),
            [mock_order_two, mock_order_three],
        )
        self.assertEqual(
            self.blotter.strategy_orders(
                69, order_status=[OrderStatus.EXECUTION_COMPLETE], matched_only=True
            ),
            [mock_order_three],
        )

    def test_strategy_selection_orders(self):
        mock_order_one = mock.Mock(
            selection_id=2, handicap=3, status=OrderStatus.EXECUTABLE, size_matched=1
        )
        mock_order_one.trade.strategy = 69
        self.blotter["12345"] = mock_order_one
        mock_order_two = mock.Mock(
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTION_COMPLETE,
            size_matched=0,
        )
        mock_order_two.trade.strategy = 69
        self.blotter["12345"] = mock_order_two
        mock_order_three = mock.Mock(
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTION_COMPLETE,
            size_matched=1,
        )
        mock_order_three.trade.strategy = 69
        self.blotter["12345"] = mock_order_three
        self.assertEqual(self.blotter.strategy_selection_orders(12, 2, 3), [])
        self.assertEqual(
            self.blotter.strategy_selection_orders(69, 2, 3),
            [mock_order_one, mock_order_two, mock_order_three],
        )
        self.assertEqual(
            self.blotter.strategy_selection_orders(
                69, 2, 3, order_status=[OrderStatus.EXECUTION_COMPLETE]
            ),
            [mock_order_two, mock_order_three],
        )
        self.assertEqual(
            self.blotter.strategy_selection_orders(
                69,
                2,
                3,
                order_status=[OrderStatus.EXECUTION_COMPLETE],
                matched_only=True,
            ),
            [mock_order_three],
        )

    def test_client_orders(self):
        mock_client_one = mock.Mock()
        mock_order_one = mock.Mock(
            client=mock_client_one,
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTABLE,
            size_matched=1,
        )
        mock_order_one.trade.strategy = 69
        self.blotter["12345"] = mock_order_one
        mock_order_two = mock.Mock(
            client=mock_client_one,
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTION_COMPLETE,
            size_matched=0,
        )
        mock_order_two.trade.strategy = 69
        self.blotter["12345"] = mock_order_two
        mock_order_three = mock.Mock(
            client=mock_client_one,
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTION_COMPLETE,
            size_matched=1,
        )
        mock_order_three.trade.strategy = 69
        self.blotter["12345"] = mock_order_three
        self.assertEqual(self.blotter.client_strategy_orders(mock_client_one, 12), [])
        self.assertEqual(
            self.blotter.client_strategy_orders(mock_client_one, 69),
            [mock_order_one, mock_order_two, mock_order_three],
        )
        self.assertEqual(
            self.blotter.client_strategy_orders(
                mock_client_one, 69, order_status=[OrderStatus.EXECUTION_COMPLETE]
            ),
            [mock_order_two, mock_order_three],
        )
        self.assertEqual(
            self.blotter.client_strategy_orders(
                mock_client_one,
                69,
                order_status=[OrderStatus.EXECUTION_COMPLETE],
                matched_only=True,
            ),
            [mock_order_three],
        )

    def test_client_strategy_orders(self):
        mock_client_one = mock.Mock()
        mock_order_one = mock.Mock(
            client=mock_client_one,
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTABLE,
            size_matched=1,
        )
        self.blotter["12345"] = mock_order_one
        mock_order_two = mock.Mock(
            client=mock_client_one,
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTION_COMPLETE,
            size_matched=0,
        )
        self.blotter["12345"] = mock_order_two
        mock_order_three = mock.Mock(
            client=mock_client_one,
            selection_id=2,
            handicap=3,
            status=OrderStatus.EXECUTION_COMPLETE,
            size_matched=1,
        )
        self.blotter["12345"] = mock_order_three
        self.assertEqual(self.blotter.client_orders(12), [])
        self.assertEqual(
            self.blotter.client_orders(mock_client_one),
            [mock_order_one, mock_order_two, mock_order_three],
        )
        self.assertEqual(
            self.blotter.client_orders(
                mock_client_one, order_status=[OrderStatus.EXECUTION_COMPLETE]
            ),
            [mock_order_two, mock_order_three],
        )
        self.assertEqual(
            self.blotter.client_orders(
                mock_client_one,
                order_status=[OrderStatus.EXECUTION_COMPLETE],
                matched_only=True,
            ),
            [mock_order_three],
        )

    def test_live_orders(self):
        self.assertEqual(list(self.blotter.live_orders), [])
        mock_order = mock.Mock(complete=False)
        self.blotter._live_orders = [mock_order]
        self.assertEqual(list(self.blotter.live_orders), [mock_order])

    def test_has_live_orders(self):
        self.assertFalse(self.blotter.has_live_orders)
        self.blotter._live_orders = [mock.Mock()]
        self.assertTrue(self.blotter.has_live_orders)

    def test_process_closed_market(self):
        mock_market_book = mock.Mock(number_of_winners=1)
        mock_runner = mock.Mock(selection_id=123, handicap=0.0)
        mock_market_book.runners = [mock_runner]
        mock_order = mock.Mock(selection_id=123, handicap=0.0)
        self.blotter._orders = {"12345": mock_order}
        self.blotter.process_closed_market(mock_market_book)
        self.assertEqual(mock_order.runner_status, mock_runner.status)
        self.assertEqual(
            mock_order.market_type, mock_market_book.market_definition.market_type
        )
        self.assertEqual(
            mock_order.each_way_divisor,
            mock_market_book.market_definition.each_way_divisor,
        )

    def test_process_cleared_orders(self):
        mock_cleared_orders = mock.Mock()
        mock_cleared_orders.orders = []
        self.assertEqual(self.blotter.process_cleared_orders(mock_cleared_orders), [])

    def test_selection_exposure(self):
        """
        Check that selection_exposure returns the absolute worse loss
        """

        def get_exposures(strategy, lookup):
            if strategy == "strategy" and lookup == (1, 2, 3):
                return {
                    "worst_possible_profit_on_win": -1.0,
                    "worst_possible_profit_on_lose": -2.0,
                }

        self.blotter.get_exposures = mock.Mock(side_effect=get_exposures)

        result = self.blotter.selection_exposure("strategy", (1, 2, 3))

        self.assertEqual(2.0, result)

    def test_selection_exposure2(self):
        """
        Check that selection_exposure returns zero if there is no risk of loss.
        """

        def get_exposures(strategy, lookup):
            if strategy == "strategy" and lookup == (1, 2, 3):
                return {
                    "worst_possible_profit_on_win": 0.0,
                    "worst_possible_profit_on_lose": 1.0,
                }

        self.blotter.get_exposures = mock.Mock(side_effect=get_exposures)

        result = self.blotter.selection_exposure("strategy", (1, 2, 3))

        self.assertEqual(0.0, result)

    def test_get_exposures(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": -2.0,
                "matched_profit_if_win": 9.2,
                "worst_possible_profit_on_lose": -2.0,
                "worst_possible_profit_on_win": 9.2,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_with_exclusion(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        mock_order_excluded = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        self.blotter["12345"] = mock_order
        self.blotter["67890"] = mock_order_excluded
        self.assertEqual(
            self.blotter.get_exposures(
                mock_strategy, mock_order.lookup, exclusion=mock_order_excluded
            ),
            {
                "matched_profit_if_lose": -2.0,
                "matched_profit_if_win": 9.2,
                "worst_possible_profit_on_lose": -2.0,
                "worst_possible_profit_on_win": 9.2,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_value_error(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=mock.Mock(ORDER_TYPE="INVALID"),
        )
        self.blotter["12345"] = mock_order

        with self.assertRaises(ValueError) as e:
            self.blotter.get_exposures(mock_strategy, mock_order.lookup)

        self.assertEqual("Unexpected order type: INVALID", e.exception.args[0])

    def test_get_exposures_with_price_none(self):
        """
        Check that get_exposures works if order.order_type.price is None.
        If order.order_type.price is None, the controls will flag the order as a violation
        and it won't be set to the exchange, so there won't be any exposure and we can ignore it.
        """
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        lookup = (self.blotter.market_id, 123, 0)
        mock_order1 = mock.Mock(
            trade=mock_trade,
            lookup=lookup,
            selection_id=123,
            handicap=0,
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        mock_order2 = mock.Mock(
            trade=mock_trade,
            lookup=lookup,
            selection_id=123,
            handicap=0,
            side="LAY",
            average_price_matched=5.6,
            size_matched=0.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=None, size=2.0),
        )
        self.blotter["12345"] = mock_order1
        self.blotter["23456"] = mock_order2
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, lookup),
            {
                "matched_profit_if_lose": -2.0,
                "matched_profit_if_win": 9.2,
                "worst_possible_profit_on_lose": -2.0,
                "worst_possible_profit_on_win": 9.2,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_no_match(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="BACK",
            average_price_matched=5.6,
            size_matched=0.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": 0.0,
                "worst_possible_profit_on_win": 0.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_from_unmatched_back(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=6, size=4.0),
            status=OrderStatus.EXECUTABLE,
            complete=False,
        )
        self.blotter["12345"] = mock_order
        # On the win side, we have 2.0 * (5.6-1.0) = 9.2
        # On the lose side, we have -2.0-2.0=-4.0
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": -2.0,
                "matched_profit_if_win": 9.2,
                "worst_possible_profit_on_lose": -4.0,
                "worst_possible_profit_on_win": 9.2,
                "worst_potential_unmatched_profit_if_lose": -2.0,
                "worst_potential_unmatched_profit_if_win": 0,
            },
        )

    def test_get_exposures_from_unmatched_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="LAY",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=6, size=4.0),
            status=OrderStatus.EXECUTABLE,
            complete=False,
        )
        self.blotter["12345"] = mock_order
        # On the win side, we have -2.0 * (5.6-1.0) -2.0 * (6.0-1.0) = -19.2
        # On the lose side, we have 2.0 from size_matched
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 2.0,
                "matched_profit_if_win": -9.2,
                "worst_possible_profit_on_lose": 2.0,
                "worst_possible_profit_on_win": -19.2,
                "worst_potential_unmatched_profit_if_lose": 0,
                "worst_potential_unmatched_profit_if_win": -10.0,
            },
        )

    def test_get_exposures_from_market_on_close_back(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="BACK",
            order_type=MarketOnCloseOrder(liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": -10.0,
                "worst_possible_profit_on_win": 0.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_from_market_on_close_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="LAY",
            order_type=MarketOnCloseOrder(liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": 0.0,
                "worst_possible_profit_on_win": -10.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_from_limit_on_close_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="LAY",
            order_type=LimitOnCloseOrder(price=1.01, liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": 0.0,
                "worst_possible_profit_on_win": -10.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_voided(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            selection_id=123,
            handicap=0,
            side="BACK",
            order_type=LimitOrder(price=5, size=10.0),
            status=OrderStatus.VIOLATION,
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": 0.0,
                "worst_possible_profit_on_win": 0.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_market_position(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        order_data = [
            # (order_id, selection_id, side, average_price_matched, size_matched, size_remaining, order_type, complete)
            (1001, 123, "BACK", 5.6, 2.0, 0.0, LimitOrder(price=5.6, size=2.0), True),
            (1002, 123, "LAY", 5.2, 3.0, 0.0, LimitOrder(price=5.2, size=3.0), True),
            (1003, 234, "LAY", 4.8, 4.0, 1.0, LimitOrder(price=4.8, size=5.0), True),
            (1004, 456, "BACK", None, 0.0, 0.0, LimitOrder(price=5.6, size=2.0), False),
            (1005, 678, "BACK", None, 0, 0, MarketOnCloseOrder(liability=6), False),
            (
                1006,
                678,
                "LAY",
                None,
                0,
                0,
                LimitOnCloseOrder(price=1.01, liability=10),
                False,
            ),
        ]
        for order in order_data:
            self.blotter[order[0]] = mock.Mock(
                trade=mock_trade,
                lookup=(self.blotter.market_id, order[1], 0),
                selection_id=order[1],
                handicap=0,
                side=order[2],
                average_price_matched=order[3],
                size_matched=order[4],
                size_remaining=order[5],
                order_type=order[6],
                complete=order[7],
            )

        mock_market_book = mock.Mock(number_of_active_runners=6, number_of_winners=1)
        self.assertEqual(  # single winner
            self.blotter.market_exposure(mock_strategy, mock_market_book), -20.2
        )
        mock_market_book = mock.Mock(number_of_active_runners=6, number_of_winners=2)
        self.assertEqual(  # muliple winners
            self.blotter.market_exposure(mock_strategy, mock_market_book), -24.6
        )
        mock_market_book = mock.Mock(number_of_active_runners=20, number_of_winners=7)
        self.assertEqual(  # num winners > num runners traded
            self.blotter.market_exposure(mock_strategy, mock_market_book), -28.6
        )

    def test_greened_market_position(self):
        mock_strategy = mock.Mock()
        mock_market_book = mock.Mock(number_of_active_runners=6, number_of_winners=1)
        mock_trade = mock.Mock(strategy=mock_strategy)
        orders = [
            # (order_id, selection_id, side, average_price_matched, size_matched, size_remaining, order_type, complete)
            (1001, 123, "BACK", 5.6, 2.0, 0.0, LimitOrder(price=5.6, size=2.0), True),
            (1002, 123, "LAY", 5.2, 2.1, 0.0, LimitOrder(price=5.2, size=2.1), True),
            (1003, 234, "BACK", 4.8, 4.0, 0.0, LimitOrder(price=4.8, size=4.0), True),
            (1004, 234, "LAY", 4, 4.2, 0.0, LimitOrder(price=4, size=4.2), True),
            (1005, 345, "BACK", 10, 2.0, 0.0, LimitOrder(price=10, size=2.0), True),
            (1006, 345, "LAY", 8, 2.2, 0.0, LimitOrder(price=8, size=2.2), True),
        ]
        for order in orders:
            self.blotter[order[0]] = mock.Mock(
                trade=mock_trade,
                lookup=(self.blotter.market_id, order[1], 0),
                selection_id=order[1],
                handicap=0,
                side=order[2],
                average_price_matched=order[3],
                size_matched=order[4],
                size_remaining=order[5],
                order_type=order[6],
                complete=order[7],
            )
        self.assertEqual(  # single winner
            self.blotter.market_exposure(mock_strategy, mock_market_book), 0.5
        )

    def test_complete_order(self):
        self.blotter._live_orders = ["test"]
        self.blotter.complete_order("test")

    def test_has_trade(self):
        self.assertFalse(self.blotter.has_trade("123"))
        self.blotter._trades["123"].append(1)
        self.assertTrue(self.blotter.has_trade("123"))

    def test__contains(self):
        self.blotter._orders = {"123": "test"}
        self.assertIn("123", self.blotter)
        self.assertNotIn("321", self.blotter)

    def test__setitem(self):
        mock_client = mock.Mock()
        mock_order = mock.Mock(
            selection_id=2, handicap=3, bet_id="456", client=mock_client
        )
        self.blotter["123"] = mock_order
        self.assertTrue(self.blotter.active)
        self.assertEqual(self.blotter._orders, {"123": mock_order})
        self.assertEqual(self.blotter._bet_id_lookup, {"456": mock_order})
        self.assertEqual(self.blotter._live_orders, [mock_order])
        self.assertEqual(self.blotter._trades, {mock_order.trade.id: [mock_order]})
        self.assertEqual(
            self.blotter._strategy_orders, {mock_order.trade.strategy: [mock_order]}
        )
        self.assertEqual(
            self.blotter._strategy_selection_orders,
            {(mock_order.trade.strategy, 2, 3): [mock_order]},
        )
        self.assertEqual(
            self.blotter._client_orders,
            {mock_client: [mock_order]},
        )
        self.assertEqual(
            self.blotter._client_strategy_orders,
            {(mock_client, mock_order.trade.strategy): [mock_order]},
        )

    def test__getitem(self):
        self.blotter._orders = {"12345": "test", "54321": "test2"}
        self.assertEqual(self.blotter["12345"], "test")
        self.assertEqual(self.blotter["54321"], "test2")

    def test__len(self):
        self.blotter._orders = {"12345": "test", "54321": "test"}
        self.assertEqual(len(self.blotter), 2)
