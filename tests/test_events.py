import unittest
from unittest import mock

from flumine.events import events


class BaseEventTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_event = mock.Mock()
        self.base_event = events.BaseEvent(self.mock_event)

    def test_init(self):
        mock_event = mock.Mock()
        base_event = events.BaseEvent(mock_event)
        self.assertIsNone(base_event.EVENT_TYPE)
        self.assertIsNone(base_event.QUEUE_TYPE)
        self.assertEqual(base_event.event, mock_event)
        self.assertIsNotNone(base_event._time_created)

    def test_elapsed_seconds(self):
        self.assertGreaterEqual(self.base_event.elapsed_seconds, 0)

    def test_str(self):
        self.base_event = events.MarketBookEvent(None)
        self.assertEqual(str(self.base_event), "<MARKET_BOOK [HANDLER]>")
