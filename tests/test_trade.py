import logging
import collections
import unittest
from unittest import mock

from flumine.order.trade import Trade, OrderError, TradeStatus


class TradeTest(unittest.TestCase):
    def setUp(self) -> None:
        logging.disable(logging.CRITICAL)
        mock_client = mock.Mock(paper_trade=False)
        self.mock_strategy = mock.Mock(client=mock_client)
        self.notes = collections.OrderedDict({"trigger": 123})
        self.trade = Trade(
            "1.234",
            567,
            1.0,
            self.mock_strategy,
            self.notes,
            12,
            34,
        )

    def test_init(self):
        self.assertEqual(self.trade.market_id, "1.234")
        self.assertEqual(self.trade.selection_id, 567)
        self.assertEqual(self.trade.handicap, 1.0)
        self.assertEqual(self.trade.strategy, self.mock_strategy)
        self.assertEqual(self.trade.notes, self.notes)
        self.assertEqual(self.trade.status_log, [])
        self.assertEqual(self.trade.orders, [])
        self.assertEqual(self.trade.offset_orders, [])
        self.assertIsNotNone(self.trade.date_time_created)
        self.assertIsNone(self.trade.date_time_complete)
        self.assertIsNone(self.trade.market_notes)
        self.assertEqual(self.trade.place_reset_seconds, 12)
        self.assertEqual(self.trade.reset_seconds, 34)

    @mock.patch("flumine.order.trade.Trade.complete_trade")
    @mock.patch(
        "flumine.order.trade.Trade.complete",
        new_callable=mock.PropertyMock,
        return_value=True,
    )
    def test__update_status(self, mock_complete, mock_complete_trade):
        self.trade._update_status(TradeStatus.COMPLETE)
        self.assertEqual(self.trade.status_log, [TradeStatus.COMPLETE])
        self.assertEqual(self.trade.status, TradeStatus.COMPLETE)
        mock_complete_trade.assert_called()

    @mock.patch("flumine.order.trade.Trade._update_status")
    def test_complete_trade(self, mock__update_status):
        self.trade.complete_trade()
        mock__update_status.assert_called_with(TradeStatus.COMPLETE)
        runner_context = self.mock_strategy.get_runner_context(
            self.trade.market_id, self.trade.selection_id, self.trade.handicap
        )
        runner_context.reset.assert_called_with(self.trade.id)
        self.assertIsNotNone(self.trade.date_time_complete)

    def test_complete(self):
        self.assertTrue(self.trade.complete)
        mock_order = mock.Mock(complete=False)
        self.trade.orders.append(mock_order)
        self.assertFalse(self.trade.complete)

    def test_trade_complete_offset(self):
        self.trade.offset_orders = [mock.Mock(complete=False)]
        self.assertFalse(self.trade.complete)
        self.trade.offset_orders = [mock.Mock(complete=True)]
        self.assertTrue(self.trade.complete)

    def test_trade_complete_replace_order(self):
        self.assertTrue(self.trade.complete)
        mock_order = mock.Mock(complete=True)
        self.trade.status = TradeStatus.COMPLETE
        self.trade.orders.append(mock_order)
        self.assertFalse(self.trade.complete)

    def test_create_order(self):
        mock_order_type = mock.Mock(EXCHANGE="SYM")
        mock_order = mock.Mock(EXCHANGE="SYM")
        self.trade.create_order(
            "BACK", mock_order_type, order=mock_order, sep="-", context={1: 2}
        )
        mock_order.assert_called_with(
            trade=self.trade,
            side="BACK",
            order_type=mock_order_type,
            handicap=self.trade.handicap,
            sep="-",
            context={1: 2},
            notes=None,
        )
        self.assertEqual(self.trade.orders, [mock_order()])

    def test_create_order_error(self):
        mock_order_type = mock.Mock(EXCHANGE="SYM")
        mock_order = mock.Mock(EXCHANGE="MYS")
        with self.assertRaises(OrderError):
            self.trade.create_order("BACK", mock_order_type, order=mock_order)

    def test_create_order_replacement(self):
        mock_order = mock.Mock(sep="-")
        replacement_order = self.trade.create_order_replacement(mock_order, 12, 2.00)
        self.assertEqual(self.trade.orders, [replacement_order])
        self.assertEqual(replacement_order.trade, self.trade)
        self.assertEqual(replacement_order.side, mock_order.side)
        self.assertEqual(replacement_order.order_type.price, 12)
        self.assertEqual(replacement_order.order_type.size, 2.00)
        self.assertEqual(
            replacement_order.order_type.persistence_type,
            mock_order.order_type.persistence_type,
        )
        self.assertEqual(replacement_order.handicap, mock_order.handicap)
        self.assertEqual(replacement_order.sep, mock_order.sep)
        self.assertEqual(replacement_order.context, mock_order.context)
        self.assertEqual(replacement_order.notes, mock_order.notes)
        self.assertEqual(replacement_order.client, mock_order.client)

    def test_create_order_from_current_limit(self):
        mock_client = mock.Mock()
        mock_current_order = mock.Mock(
            order_type="LIMIT", placed_date=12, matched_date=None, cancelled_date=34
        )
        order = self.trade.create_order_from_current(
            mock_client, mock_current_order, "12345"
        )
        self.assertEqual(order.bet_id, mock_current_order.bet_id)
        self.assertEqual(order.id, "12345")
        self.assertEqual(order.client, mock_client)
        self.assertEqual(self.trade.orders, [order])
        self.assertEqual(order.date_time_created, 12)
        self.assertEqual(order.date_time_execution_complete, 34)

    def test_create_order_from_current_limit_on_close(self):
        mock_client = mock.Mock()
        mock_current_order = mock.Mock(order_type="LIMIT_ON_CLOSE")
        order = self.trade.create_order_from_current(
            mock_client, mock_current_order, "12345"
        )
        self.assertEqual(order.bet_id, mock_current_order.bet_id)
        self.assertEqual(order.id, "12345")
        self.assertEqual(order.client, mock_client)
        self.assertEqual(self.trade.orders, [order])

    def test_create_order_from_current_market_on_close(self):
        mock_client = mock.Mock()
        mock_current_order = mock.Mock(order_type="MARKET_ON_CLOSE")
        order = self.trade.create_order_from_current(
            mock_client, mock_current_order, "12345"
        )
        self.assertEqual(order.bet_id, mock_current_order.bet_id)
        self.assertEqual(order.id, "12345")
        self.assertEqual(order.client, mock_client)
        self.assertEqual(self.trade.orders, [order])

    def test_create_order_from_current_unknown(self):
        mock_client = mock.Mock()
        mock_current_order = mock.Mock(order_type="BE")
        with self.assertRaises(NotImplementedError):
            self.trade.create_order_from_current(
                mock_client, mock_current_order, "12345"
            )

    def test_notes_str(self):
        self.trade.notes = collections.OrderedDict({"1": 1, 2: "2", 3: 3, 4: "four"})
        self.assertEqual(self.trade.notes_str, "1,2,3,four")
        self.trade.notes = collections.OrderedDict()
        self.assertEqual(self.trade.notes_str, "")

    def test_info(self):
        self.trade.status_log = [TradeStatus.PENDING, TradeStatus.COMPLETE]
        self.assertEqual(
            self.trade.info,
            {
                "id": str(self.trade.id),
                "orders": [],
                "offset_orders": [],
                "place_reset_seconds": 12,
                "reset_seconds": 34,
                "strategy": str(self.mock_strategy),
                "notes": "123",
                "market_notes": None,
                "status": "Live",
                "status_log": "Pending, Complete",
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
