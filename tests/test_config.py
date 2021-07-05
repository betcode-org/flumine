import unittest

from flumine import config


class ConfigTest(unittest.TestCase):
    def test_init(self):
        self.assertFalse(config.simulated)
        self.assertIsInstance(config.hostname, str)
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
