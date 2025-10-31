import unittest
import datetime
from unittest import mock

from flumine.simulation import utils


class NewDateTimeTest(unittest.TestCase):
    @mock.patch("flumine.simulation.utils.config")
    def test_utcnow(self, mock_config):
        mock_config.current_time = 123
        x = utils.NewDateTime
        self.assertEqual(x.utcnow(), 123)

    @mock.patch("flumine.simulation.utils.config")
    def test_now(self, mock_config):
        mock_config.current_time = 123
        x = utils.NewDateTime
        self.assertEqual(x.now(datetime.timezone.utc), 123)


class SimulatedDateTimeTest(unittest.TestCase):
    def setUp(self):
        self.s = utils.SimulatedDateTime()

    def test_init(self):
        self.assertIsNone(self.s._real_datetime)

    @mock.patch("flumine.simulation.utils.config")
    def test_reset_real_datetime(self, mock_config):
        mock_real_datetime = mock.Mock()
        self.s._real_datetime = mock_real_datetime
        self.s.reset_real_datetime()
        mock_real_datetime.now.assert_called()
        self.assertEqual(
            mock_config.current_time, mock_real_datetime.now(datetime.timezone.utc)
        )

    @mock.patch("flumine.simulation.utils.config")
    def test_call(self, mock_config):
        mock_dt = mock.Mock()
        self.s(mock_dt)
        self.assertEqual(mock_config.current_time, mock_dt)

    @mock.patch("flumine.simulation.utils.config")
    def test_context_manager(self, mock_config):
        with self.s as datetime:
            mock_config.current_time = 456
            self.assertEqual(datetime.utcnow(), 456)
            self.assertEqual(datetime.now(), 456)
        import datetime

        self.assertIsInstance(datetime.datetime.utcnow(), datetime.datetime)
        self.assertIsInstance(datetime.datetime.now(), datetime.datetime)
