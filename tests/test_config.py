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
