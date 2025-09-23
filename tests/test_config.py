import unittest

from flumine import config


class ConfigTest(unittest.TestCase):
    def test_init(self):
        self.assertFalse(config.simulated)
        self.assertTrue(config.simulated_strategy_isolation)
        self.assertFalse(config.simulation_available_prices)
        self.assertIsNone(config.customer_strategy_ref)
        self.assertIsInstance(config.process_id, int)
        self.assertIsNone(config.current_time)
        self.assertFalse(config.raise_errors)
        self.assertEqual(config.max_execution_workers, 32)
        self.assertFalse(config.async_place_orders)
        self.assertEqual(config.place_latency, 0.120)
        self.assertEqual(config.cancel_latency, 0.170)
        self.assertEqual(config.update_latency, 0.150)
        self.assertEqual(config.replace_latency, 0.280)
        self.assertEqual(config.order_sep, "-")
        self.assertEqual(config.execution_retry_attempts, 10)
