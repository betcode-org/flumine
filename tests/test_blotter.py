import unittest
from unittest import mock

from flumine.markets.blotter import Blotter
from flumine.order.order import OrderStatus
from flumine.order.ordertype import MarketOnCloseOrder, LimitOrder, LimitOnCloseOrder


class BlotterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.blotter = Blotter("1.23")

    def test_init(self):
        self.assertEqual(self.blotter.market_id, "1.23")
        self.assertEqual(self.blotter._orders, {})
        self.assertEqual(self.blotter._live_orders, [])

    def test_strategy_orders(self):
        mock_order = mock.Mock()
        mock_order.trade.strategy = 69
        self.blotter["12345"] = mock_order
        self.assertEqual(self.blotter.strategy_orders(12), [])
        self.assertEqual(self.blotter.strategy_orders(69), [mock_order])

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
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock(selection_id=123, handicap=0.0)
        mock_market_book.runners = [mock_runner]
        mock_order = mock.Mock(selection_id=123, handicap=0.0)
        self.blotter._orders = {"12345": mock_order}
        self.blotter.process_closed_market(mock_market_book)
        self.assertEqual(mock_order.runner_status, mock_runner.status)

    def test_process_cleared_orders(self):
        mock_cleared_orders = mock.Mock()
        self.assertEqual(self.blotter.process_cleared_orders(mock_cleared_orders), [])

    def test_selection_exposure(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup),
            2.0,
        )

    def test_selection_exposure_raises_value_error(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=mock.Mock(ORDER_TYPE="INVALID"),
        )
        self.blotter["12345"] = mock_order

        with self.assertRaises(ValueError) as e:
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup)

        self.assertEqual("Unexpected order type: INVALID", e.exception.args[0])

    def test_selection_exposure_with_price_none(self):
        """
        Check that selection_exposure works if order.order_type.price is None.
        If order.order_type.price is None, the controls will flag the order as a violation
        and it won't be set to the exchange, so there won't be any exposure and we can ignore it.
        :return:
        """
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        lookup = (self.blotter.market_id, 123, 0)
        mock_order1 = mock.Mock(
            trade=mock_trade,
            lookup=lookup,
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        mock_order2 = mock.Mock(
            trade=mock_trade,
            lookup=lookup,
            side="LAY",
            average_price_matched=5.6,
            size_matched=0.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=None, size=2.0),
        )
        self.blotter["12345"] = mock_order1
        self.blotter["23456"] = mock_order2
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, lookup),
            2.0,
        )

    def test_selection_exposure_no_match(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=0.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup),
            0.0,
        )

    def test_selection_exposure_from_unmatched_back(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=6, size=4.0),
        )
        self.blotter["12345"] = mock_order
        # On the win side, we have 2.0 * (5.6-1.0) = 9.2
        # On the lose side, we have -2.0-2.0=-4.0
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup),
            4.0,
        )

    def test_selection_exposure_from_unmatched_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="LAY",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=6, size=4.0),
        )
        self.blotter["12345"] = mock_order
        # On the win side, we have -2.0 * (5.6-1.0) -2.0 * (6.0-1.0) = -19.2
        # On the lose side, we have 2.0 from size_matched
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup),
            19.2,
        )

    def test_selection_exposure_from_market_on_close_back(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            order_type=MarketOnCloseOrder(liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup),
            10.0,
        )

    def test_selection_exposure_from_market_on_close_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="LAY",
            order_type=MarketOnCloseOrder(liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup),
            10.0,
        )

    def test_selection_exposure_from_limit_on_close_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="LAY",
            order_type=LimitOnCloseOrder(price=1.01, liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup),
            10.0,
        )

    def test_selection_exposure_voided(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            order_type=LimitOrder(price=5, size=10.0),
            status=OrderStatus.VIOLATION,
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.selection_exposure(mock_strategy, mock_order.lookup),
            0,
        )

    def test_complete_order(self):
        self.blotter._live_orders = ["test"]
        self.blotter.complete_order("test")

    def test__contains(self):
        self.blotter._orders = {"123": "test"}
        self.assertIn("123", self.blotter)
        self.assertNotIn("321", self.blotter)

    def test__setitem(self):
        mock_order = mock.Mock()
        self.blotter["123"] = mock_order
        self.assertEqual(self.blotter._orders, {"123": mock_order})
        self.assertEqual(self.blotter._live_orders, [mock_order])
        self.assertEqual(
            self.blotter._strategy_orders, {mock_order.trade.strategy: [mock_order]}
        )

    def test__getitem(self):
        self.blotter._orders = {"12345": "test", "54321": "test2"}
        self.assertEqual(self.blotter["12345"], "test")
        self.assertEqual(self.blotter["54321"], "test2")

    def test__len(self):
        self.blotter._orders = {"12345": "test", "54321": "test"}
        self.assertEqual(len(self.blotter), 2)
