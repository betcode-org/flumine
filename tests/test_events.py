import unittest
from unittest import mock

from flumine.events import events


class BaseEventTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_event = mock.Mock()
        self.base_event = events.BaseEvent(self.mock_event, 123)

    def test_init(self):
        self.assertIsNone(self.base_event.EVENT_TYPE)
        self.assertIsNone(self.base_event.QUEUE_TYPE)
        self.assertEqual(self.base_event.event, self.mock_event)
        self.assertEqual(self.base_event.exchange, 123)
        self.assertIsNotNone(self.base_event._time_created)

    def test_elapsed_seconds(self):
        self.assertGreaterEqual(self.base_event.elapsed_seconds, 0)

    def test_str(self):
        self.base_event = events.MarketBookEvent(None)
        self.assertEqual(str(self.base_event), "<MARKET_BOOK [HANDLER]>")
