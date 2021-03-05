import uuid
import unittest
import datetime

from flumine.strategy.runnercontext import RunnerContext


class RunnerContextTest(unittest.TestCase):
    def setUp(self):
        self.id_ = str(uuid.uuid1())
        self.context = RunnerContext(12345)

    def test_init(self):
        self.assertEqual(self.context.selection_id, 12345)
        self.assertFalse(self.context.invested)
        self.assertIsNone(self.context.datetime_last_placed)
        self.assertIsNone(self.context.datetime_last_reset)
        self.assertEqual(self.context.trades, [])
        self.assertEqual(self.context.live_trades, [])

    def test_place(self):
        self.context.place(self.id_)
        self.context.place(self.id_)  # append is ignored
        self.assertTrue(self.context.invested)
        self.assertIsNotNone(self.context.datetime_last_placed)
        self.assertEqual(self.context.trades, [self.id_])
        self.assertEqual(self.context.live_trades, [self.id_])

    def test_reset(self):
        self.context.live_trades = [self.id_]
        self.context.reset(self.id_)
        self.assertIsNotNone(self.context.datetime_last_reset)
        self.assertEqual(self.context.live_trades, [])

    def test_reset_error(self):
        self.context.reset(self.id_)
        self.assertIsNotNone(self.context.datetime_last_reset)
        self.assertEqual(self.context.live_trades, [])

    def test_executable_orders(self):
        self.assertFalse(self.context.executable_orders)
        self.context.live_trades = [self.id_]
        self.assertTrue(self.context.executable_orders)

    def test_trade_count(self):
        self.assertEqual(self.context.trade_count, 0)
        self.context.trades = [self.id_]
        self.assertEqual(self.context.trade_count, 1)

    def test_live_trade_count(self):
        self.assertEqual(self.context.live_trade_count, 0)
        self.context.live_trades = [self.id_]
        self.assertEqual(self.context.live_trade_count, 1)

    def test_placed_elapsed_seconds(self):
        self.assertIsNone(self.context.placed_elapsed_seconds)
        self.context.datetime_last_placed = datetime.datetime.utcnow()
        self.assertGreaterEqual(self.context.placed_elapsed_seconds, 0)

    def test_reset_elapsed_seconds(self):
        self.assertIsNone(self.context.reset_elapsed_seconds)
        self.context.datetime_last_reset = datetime.datetime.utcnow()
        self.assertGreaterEqual(self.context.reset_elapsed_seconds, 0)
