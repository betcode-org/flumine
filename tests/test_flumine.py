import unittest
from unittest import mock

from flumine import Flumine
from flumine.events import events
from flumine.order.orderpackage import BaseOrderPackage


class FlumineTest(unittest.TestCase):
    def setUp(self):
        self.mock_trading = mock.Mock()
        self.flumine = Flumine(self.mock_trading)

    @mock.patch("flumine.flumine.Flumine._process_custom_event")
    @mock.patch("flumine.flumine.Flumine._process_cleared_orders")
    @mock.patch("flumine.flumine.Flumine._process_cleared_markets")
    @mock.patch("flumine.flumine.Flumine._process_close_market")
    @mock.patch("flumine.flumine.Flumine._process_order_package")
    @mock.patch("flumine.flumine.Flumine._process_current_orders")
    @mock.patch("flumine.flumine.Flumine._process_end_flumine")
    @mock.patch("flumine.flumine.Flumine._process_market_catalogues")
    @mock.patch("flumine.flumine.Flumine._process_raw_data")
    @mock.patch("flumine.flumine.Flumine._process_market_books")
    def test_run(
        self,
        mock__process_market_books,
        mock__process_raw_data,
        mock__process_market_catalogues,
        mock__process_end_flumine,
        mock__process_current_orders,
        mock__process_order_package,
        mock__process_close_market,
        mock__process_cleared_markets,
        mock__process_cleared_orders,
        mock__process_custom_event,
    ):
        mock_events = [
            events.MarketCatalogueEvent(None),
            events.MarketBookEvent(None),
            events.RawDataEvent(None),
            events.CurrentOrdersEvent(None),
            BaseOrderPackage(None, "1.123", [], "12", None),
            events.ClearedMarketsEvent(None),
            events.ClearedOrdersEvent(None),
            events.CloseMarketEvent(None),
            events.CustomEvent(None, None),
            events.NewDayEvent(None),
            events.TerminationEvent(None),
        ]
        for i in mock_events:
            self.flumine.handler_queue.put(i)
        self.flumine.run()

        mock__process_market_books.assert_called_with(mock_events[1])
        mock__process_raw_data.assert_called_with(mock_events[2])
        mock__process_market_catalogues.assert_called_with(mock_events[0])
        mock__process_end_flumine.assert_called_with()
        mock__process_current_orders.assert_called_with(mock_events[3])
        mock__process_order_package.assert_called_with(mock_events[4])
        mock__process_close_market.assert_called_with(mock_events[7])
        mock__process_cleared_markets.assert_called_with(mock_events[5])
        mock__process_cleared_orders.assert_called_with(mock_events[6])
        mock__process_custom_event.assert_called_with(mock_events[8])

    def test__add_default_workers(self):
        self.flumine._add_default_workers()
        self.assertEqual(len(self.flumine._workers), 4)

    def test_str(self):
        assert str(self.flumine) == "<Flumine>"

    def test_repr(self):
        assert repr(self.flumine) == "<Flumine>"
