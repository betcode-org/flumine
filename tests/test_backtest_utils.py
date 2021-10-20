import unittest

from flumine.backtest import utils


class NewDateTimeTest(unittest.TestCase):
    def test_new_date_time(self):
        utils.config.current_time = 123
        x = utils.NewDateTime
        self.assertEqual(x.utcnow(), 123)


class SimulatedDateTimeTest(unittest.TestCase):
    def setUp(self):
        self.s = utils.SimulatedDateTime()

    def test_init(self):
        self.assertIsNone(self.s._real_datetime)

    def test_context_manager(self):
        with self.s as datetime:
            utils.config.current_time = 456
            self.assertEqual(datetime.utcnow(), 456)
        import datetime

        self.assertIsInstance(datetime.datetime.utcnow(), datetime.datetime)

    def tearDown(self) -> None:
        utils.config.current_time = None
