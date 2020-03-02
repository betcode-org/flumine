import unittest
from unittest import mock

from flumine.flumine import Flumine
from flumine.event import event


class FlumineTest(unittest.TestCase):
    def setUp(self):
        self.mock_trading = mock.Mock()
        self.flumine = Flumine(self.mock_trading)

    @mock.patch("flumine.flumine.Flumine._process_end_flumine")
    @mock.patch("flumine.flumine.Flumine._process_raw_data")
    @mock.patch("flumine.flumine.Flumine._process_market_books")
    def test_run(
        self,
        mock__process_market_books,
        mock__process_raw_data,
        mock__process_end_flumine,
    ):
        events = [
            event.MarketCatalogueEvent(None),
            event.MarketBookEvent(None),
            event.RawDataEvent(None),
            event.CurrentOrdersEvent(None),
            event.ClearedMarketsEvent(None),
            event.ClearedOrdersEvent(None),
            event.CloseMarketEvent(None),
            event.StrategyResetEvent(None),
            event.CustomEvent(None),
            event.NewDayEvent(None),
            event.EventType.TERMINATOR,
        ]
        for i in events:
            self.flumine.handler_queue.put(i)
        self.flumine.run()

        mock__process_market_books.assert_called_with(events[1])
        mock__process_raw_data.assert_called_with(events[2])
        mock__process_end_flumine.assert_called_with()

    def test_str(self):
        assert str(self.flumine) == "<Flumine [not running]>"

    def test_repr(self):
        assert repr(self.flumine) == "<Flumine>"
