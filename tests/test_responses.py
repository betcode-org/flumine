import unittest
from unittest import mock

from flumine.order.responses import Responses


class ResponsesTest(unittest.TestCase):
    def setUp(self):
        self.responses = Responses()

    def test_init(self):
        self.assertIsNotNone(self.responses.date_time_created)
        self.assertIsNone(self.responses.place_response)
        self.assertEqual(self.responses.cancel_responses, [])
        self.assertEqual(self.responses.replace_responses, [])
        self.assertEqual(self.responses.cancel_responses, [])
        self.assertIsNone(self.responses._date_time_placed)
        self.assertIsNone(self.responses.current_order)

    def test_placed(self):
        self.responses.placed(12)
        self.assertIsNotNone(self.responses._date_time_placed)
        self.assertEqual(self.responses.place_response, 12)

    def test_cancelled(self):
        self.responses.cancelled(12)
        self.assertEqual(self.responses.cancel_responses, [12])

    def test_replaced(self):
        self.responses.replaced(12)
        # self.assertIsNotNone(self.responses.date_time_placed)
        self.assertEqual(self.responses.replace_responses, [12])

    def test_updated(self):
        self.responses.updated(12)
        self.assertEqual(self.responses.update_responses, [12])

    def test_date_time_placed(self):
        self.assertIsNone(self.responses.date_time_placed)
        self.responses._date_time_placed = 1
        self.responses.current_order = mock.Mock(placed_date=2)
        self.assertEqual(self.responses.date_time_placed, 1)
        self.responses._date_time_placed = None
        self.assertEqual(self.responses.date_time_placed, 2)
        self.responses._date_time_placed = None
        self.responses.current_order = None
        self.assertIsNone(self.responses.date_time_placed)
