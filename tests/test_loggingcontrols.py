import unittest
from unittest import mock
from queue import Queue

from flumine.controls.loggingcontrols import LoggingControl, EventType


class TestLoggingControl(unittest.TestCase):
    def setUp(self):
        self.logging_control = LoggingControl()

    def test_init(self):
        self.assertIsInstance(self.logging_control.logging_queue, Queue)
        self.assertEqual(self.logging_control.cache, [])
        self.assertEqual(self.logging_control.NAME, "LOGGING_CONTROL")

    def test_run(self):
        self.logging_control.logging_queue.put(None)
        self.logging_control.run()

    def test_run_error(self):
        self.logging_control.logging_queue.put(1)
        self.logging_control.logging_queue.put(None)
        self.logging_control.run()

    @mock.patch("flumine.controls.loggingcontrols.LoggingControl._process_config")
    def test_process_event_config(self, mock_process_config):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.CONFIG
        self.logging_control.process_event(mock_event)
        mock_process_config.assert_called_with(mock_event)

    @mock.patch("flumine.controls.loggingcontrols.LoggingControl._process_strategy")
    def test_process_event_strategy(self, mock_process_strategy):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.STRATEGY
        self.logging_control.process_event(mock_event)
        mock_process_strategy.assert_called_with(mock_event)

    @mock.patch("flumine.controls.loggingcontrols.LoggingControl._process_market")
    def test_process_event_market(self, _process_market):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.MARKET
        self.logging_control.process_event(mock_event)
        _process_market.assert_called_with(mock_event)

    @mock.patch("flumine.controls.loggingcontrols.LoggingControl._process_trade")
    def test_process_event_trade(self, _process_trade):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.TRADE
        self.logging_control.process_event(mock_event)
        _process_trade.assert_called_with(mock_event)

    @mock.patch("flumine.controls.loggingcontrols.LoggingControl._process_order")
    def test_process_event_order(self, _process_order):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.ORDER
        self.logging_control.process_event(mock_event)
        _process_order.assert_called_with(mock_event)

    @mock.patch("flumine.controls.loggingcontrols.LoggingControl._process_balance")
    def test_process_event_balance(self, _process_balance):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.BALANCE
        self.logging_control.process_event(mock_event)
        _process_balance.assert_called_with(mock_event)

    @mock.patch(
        "flumine.controls.loggingcontrols.LoggingControl._process_cleared_orders"
    )
    def test_process_event_cleared(self, _process_cleared_orders):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.CLEARED_ORDERS
        self.logging_control.process_event(mock_event)
        _process_cleared_orders.assert_called_with(mock_event)

    @mock.patch(
        "flumine.controls.loggingcontrols.LoggingControl._process_cleared_orders_meta"
    )
    def test_process_event_cleared_orders_meta(self, _process_cleared_orders_meta):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.CLEARED_ORDERS_META
        self.logging_control.process_event(mock_event)
        _process_cleared_orders_meta.assert_called_with(mock_event)

    @mock.patch(
        "flumine.controls.loggingcontrols.LoggingControl._process_cleared_markets"
    )
    def test_process_event_cleared_markets(self, _process_cleared_markets):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.CLEARED_MARKETS
        self.logging_control.process_event(mock_event)
        _process_cleared_markets.assert_called_with(mock_event)

    @mock.patch(
        "flumine.controls.loggingcontrols.LoggingControl._process_closed_market"
    )
    def test_process_event_closed(self, _closed_market):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.CLOSE_MARKET
        self.logging_control.process_event(mock_event)
        _closed_market.assert_called_with(mock_event)

    @mock.patch("flumine.controls.loggingcontrols.LoggingControl._process_custom_event")
    def test_process_event_custom_event(self, _closed_market):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.CUSTOM_EVENT
        self.logging_control.process_event(mock_event)
        _closed_market.assert_called_with(mock_event)

    @mock.patch("flumine.controls.loggingcontrols.LoggingControl._process_end_flumine")
    def test_process_event_end(self, _end_flumine):
        mock_event = mock.Mock()
        mock_event.EVENT_TYPE = EventType.TERMINATOR
        self.logging_control.process_event(mock_event)
        _end_flumine.assert_called_with(mock_event)
        self.assertIsNone(self.logging_control.logging_queue.get())

    def test_process_config(self):
        self.logging_control._process_config(None)

    def test_process_strategy(self):
        self.logging_control._process_strategy(None)

    def test_process_market(self):
        self.logging_control._process_market(None)

    def test_process_trade(self):
        self.logging_control._process_trade(None)

    def test_process_order(self):
        self.logging_control._process_order(None)

    def test_process_balance(self):
        self.logging_control._process_balance(None)

    def test_process_cleared_orders(self):
        self.logging_control._process_cleared_orders(None)

    def test_process_cleared_orders_meta(self):
        self.logging_control._process_cleared_orders_meta(None)

    def test_process_cleared_markets(self):
        self.logging_control._process_cleared_markets(None)

    def test_process_closed_market(self):
        self.logging_control._process_closed_market(None)

    def test_process_custom_event(self):
        self.logging_control._process_custom_event(None)

    def test_process_end_flumine(self):
        self.logging_control._process_end_flumine(None)
