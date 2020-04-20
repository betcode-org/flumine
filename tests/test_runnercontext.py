import unittest
import datetime

from flumine.strategy.runnercontext import RunnerContext


class RunnerContextTest(unittest.TestCase):
    def setUp(self):
        self.context = RunnerContext(12345)

    def test_init(self):
        self.assertEqual(self.context.selection_id, 12345)

        self.assertFalse(self.context.invested)
        self.assertIsNone(self.context.datetime_last_placed)
        self.assertIsNone(self.context.datetime_last_reset)
        self.assertEqual(self.context.trade_count, 0)
        self.assertEqual(self.context.live_trade_count, 0)

    def test_place(self):
        self.context.place()
        self.assertTrue(self.context.invested)
        self.assertIsNotNone(self.context.datetime_last_placed)
        self.assertEqual(self.context.trade_count, 1)
        self.assertEqual(self.context.live_trade_count, 1)

    def test_reset(self):
        self.context.invested = True
        self.context.live_trade_count = 1
        self.context.reset()
        self.assertFalse(self.context.invested)
        self.assertIsNotNone(self.context.datetime_last_reset)
        self.assertEqual(self.context.live_trade_count, 0)

    def test_placed_elapsed_seconds(self):
        self.assertIsNone(self.context.placed_elapsed_seconds)
        self.context.datetime_last_placed = datetime.datetime.utcnow()
        self.assertGreaterEqual(self.context.placed_elapsed_seconds, 0)

    def test_reset_elapsed_seconds(self):
        self.assertIsNone(self.context.reset_elapsed_seconds)
        self.context.datetime_last_reset = datetime.datetime.utcnow()
        self.assertGreaterEqual(self.context.reset_elapsed_seconds, 0)
