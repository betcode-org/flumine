import unittest
from unittest import mock

from flumine.markets.blotter import Blotter, OrderStatus, OrderPackageType


class BlotterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_market = mock.Mock()
        self.blotter = Blotter(self.mock_market)

    def test_init(self):
        self.assertEqual(self.blotter.market, self.mock_market)
        self.assertEqual(self.blotter._orders, {})
        self.assertEqual(self.blotter.pending_place, [])
        self.assertEqual(self.blotter.pending_cancel, [])
        self.assertEqual(self.blotter.pending_update, [])
        self.assertEqual(self.blotter.pending_replace, [])

    def test_strategy_orders(self):
        mock_order = mock.Mock()
        mock_order.trade.strategy = 69
        self.blotter._orders = {"12345": mock_order}
        self.assertEqual(self.blotter.strategy_orders(12), [])
        self.assertEqual(self.blotter.strategy_orders(69), [mock_order])

    @mock.patch("flumine.markets.blotter.Blotter._create_packages")
    def test_process_orders(self, mock__create_packages):
        mock_client = mock.Mock()
        self.blotter.pending_place = [1]
        self.assertEqual(
            self.blotter.process_orders(mock_client), mock__create_packages().__radd__()
        )
        self.blotter.pending_place = []
        self.blotter.pending_cancel = [2]
        self.assertEqual(
            self.blotter.process_orders(mock_client), mock__create_packages().__radd__()
        )
        self.blotter.pending_cancel = []
        self.blotter.pending_update = [3]
        self.assertEqual(
            self.blotter.process_orders(mock_client), mock__create_packages().__radd__()
        )
        self.blotter.pending_update = []
        self.blotter.pending_replace = [4]
        self.assertEqual(
            self.blotter.process_orders(mock_client), mock__create_packages().__radd__()
        )

    @mock.patch("flumine.markets.blotter.BetfairOrderPackage")
    def test___create_packages(self, mock_cls):
        mock_client = mock.Mock()
        mock_order = mock.Mock()
        mock_orders = [mock_order]
        packages = self.blotter._create_packages(
            mock_client, mock_orders, OrderPackageType.PLACE
        )
        self.assertEqual(
            packages,
            [
                mock_cls(
                    client=None,
                    market_id=self.blotter.market_id,
                    orders=mock_orders,
                    package_type=OrderPackageType.PLACE,
                )
            ],
        )
        self.assertEqual(mock_orders, [])

    def test_live_orders(self):
        self.assertFalse(self.blotter.live_orders)
        mock_order = mock.Mock()
        mock_order.status = OrderStatus.EXECUTABLE
        self.blotter._orders = {"12345": mock_order}
        self.assertTrue(self.blotter.live_orders)

    def test_live_orders_trade(self):
        self.assertFalse(self.blotter.live_orders)
        mock_order = mock.Mock()
        mock_order.trade.trade_complete = False
        mock_order.status = OrderStatus.EXECUTION_COMPLETE
        self.blotter._orders = {"12345": mock_order}
        self.assertTrue(self.blotter.live_orders)

    def test_process_closed_market(self):
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock(selection_id=123, handicap=0.0)
        mock_market_book.runners = [mock_runner]
        mock_order = mock.Mock(selection_id=123, handicap=0.0)
        self.blotter._orders = {"12345": mock_order}
        self.blotter.process_closed_market(mock_market_book)
        self.assertEqual(mock_order.runner_status, mock_runner.status)

    def test_selection_exposure(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
        )
        self.blotter._orders = {"12345": mock_order}

        self.assertEqual(
            self.blotter.selection_exposure(
                mock_strategy, (self.blotter.market_id, 123, 0)
            ),
            -2,
        )

    def test_market_id(self):
        self.assertEqual(self.blotter.market_id, self.mock_market.market_id)

    def test__contains(self):
        self.blotter._orders = {"123": "test"}
        self.assertIn("123", self.blotter)
        self.assertNotIn("321", self.blotter)

    def test__setitem(self):
        self.blotter["123"] = "test"
        self.assertEqual(self.blotter._orders, {"123": "test"})

    def test__getitem(self):
        self.blotter._orders = {"12345": "test", "54321": "test2"}
        self.assertEqual(self.blotter["12345"], "test")
        self.assertEqual(self.blotter["54321"], "test2")

    def test__len(self):
        self.blotter._orders = {"12345": "test", "54321": "test"}
        self.assertEqual(len(self.blotter), 2)
