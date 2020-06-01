import logging
import collections
import unittest
from unittest import mock

from flumine.order.trade import Trade, OrderError, OrderStatus, TradeStatus


class TradeTest(unittest.TestCase):
    def setUp(self) -> None:
        logging.disable(logging.CRITICAL)
        self.mock_strategy = mock.Mock()
        self.mock_fill_kill = mock.Mock()
        self.mock_offset = mock.Mock()
        self.mock_green = mock.Mock()
        self.mock_stop = mock.Mock()
        self.notes = collections.OrderedDict({"trigger": 123})
        self.trade = Trade(
            "1.234",
            567,
            1.0,
            self.mock_strategy,
            self.notes,
            self.mock_fill_kill,
            self.mock_offset,
            self.mock_green,
            self.mock_stop,
        )

    def test_init(self):
        self.assertEqual(self.trade.market_id, "1.234")
        self.assertEqual(self.trade.selection_id, 567)
        self.assertEqual(self.trade.handicap, 1.0)
        self.assertEqual(self.trade.strategy, self.mock_strategy)
        self.assertEqual(self.trade.notes, self.notes)
        self.assertEqual(self.trade.fill_kill, self.mock_fill_kill)
        self.assertEqual(self.trade.offset, self.mock_offset)
        self.assertEqual(self.trade.green, self.mock_green)
        self.assertEqual(self.trade.stop, self.mock_stop)
        self.assertEqual(self.trade.status_log, [])
        self.assertEqual(self.trade.orders, [])
        self.assertEqual(self.trade.offset_orders, [])

    def test__update_status(self):
        self.trade._update_status(TradeStatus.COMPLETE)
        self.assertEqual(self.trade.status_log, [TradeStatus.COMPLETE])
        self.assertEqual(self.trade.status, TradeStatus.COMPLETE)

    @mock.patch("flumine.order.trade.Trade._update_status")
    def test_complete(self, mock__update_status):
        self.trade.complete()
        mock__update_status.assert_called_with(TradeStatus.COMPLETE)
        runner_context = self.mock_strategy.get_runner_context(
            self.trade.market_id, self.trade.selection_id, self.trade.handicap
        )
        runner_context.reset.assert_called_with()

    def test_trade_complete(self):
        self.assertTrue(self.trade.trade_complete)
        mock_order = mock.Mock(status=OrderStatus.PENDING)
        self.trade.orders.append(mock_order)
        self.assertFalse(self.trade.trade_complete)

    def test_trade_complete_offset(self):
        self.trade.offset_orders = [1]
        self.assertFalse(self.trade.trade_complete)

    def test_trade_complete_replace_order(self):
        self.assertTrue(self.trade.trade_complete)
        mock_order = mock.Mock(status=OrderStatus.EXECUTION_COMPLETE)
        self.trade.status = TradeStatus.COMPLETE
        self.trade.orders.append(mock_order)
        self.assertFalse(self.trade.trade_complete)

    def test_create_order(self):
        mock_order_type = mock.Mock()
        mock_order_type.EXCHANGE = "SYM"
        mock_order = mock.Mock()
        mock_order.EXCHANGE = "SYM"
        self.trade.create_order("BACK", mock_order_type, handicap=1, order=mock_order)
        self.assertEqual(self.trade.orders, [mock_order()])

    def test_create_order_error(self):
        mock_order_type = mock.Mock()
        mock_order_type.EXCHANGE = "SYM"
        mock_order = mock.Mock()
        mock_order.EXCHANGE = "MYS"
        with self.assertRaises(OrderError):
            self.trade.create_order(
                "BACK", mock_order_type, handicap=1, order=mock_order
            )

    def test_create_order_replacement(self):
        mock_order = mock.Mock()
        replacement_order = self.trade.create_order_replacement(mock_order, 12)
        self.assertEqual(self.trade.orders, [replacement_order])

    def test_create_order_from_current_limit(self):
        mock_current_order = mock.Mock()
        mock_current_order.order_type = "LIMIT"
        order = self.trade.create_order_from_current(mock_current_order, "12345")
        self.assertEqual(order.bet_id, mock_current_order.bet_id)
        self.assertEqual(order.id, "12345")
        self.assertEqual(self.trade.orders, [order])

    def test_create_order_from_current_limit_on_close(self):
        mock_current_order = mock.Mock()
        mock_current_order.order_type = "LIMIT_ON_CLOSE"
        with self.assertRaises(NotImplementedError):
            self.trade.create_order_from_current(mock_current_order, "12345")

    def test_create_order_from_current_market_on_close(self):
        mock_current_order = mock.Mock()
        mock_current_order.order_type = "MARKET_ON_CLOSE"
        with self.assertRaises(NotImplementedError):
            self.trade.create_order_from_current(mock_current_order, "12345")

    def test_notes_str(self):
        self.trade.notes = collections.OrderedDict({"1": 1, 2: "2", 3: 3, 4: "four"})
        # self.assertEqual(self.trade.notes_str, "1,2,3,four")
        self.trade.notes = collections.OrderedDict()
        self.assertEqual(self.trade.notes_str, "")

    def test_info(self):
        self.assertEqual(
            self.trade.info,
            {
                "id": self.trade.id,
                "orders": [],
                "status": TradeStatus.LIVE,
                "strategy": self.mock_strategy,
                "notes": "123",
            },
        )

    @mock.patch("flumine.order.trade.Trade._update_status")
    def test_enter_exit(self, mock__update_status):
        with self.trade:
            mock__update_status.assert_called_with(TradeStatus.PENDING)
        mock__update_status.assert_called_with(TradeStatus.LIVE)

    @mock.patch("flumine.order.trade.Trade._update_status")
    def test_enter_error(self, mock__update_status):
        with self.assertRaises(ValueError):
            with self.trade:
                raise ValueError()
        mock__update_status.assert_called_with(TradeStatus.PENDING)
