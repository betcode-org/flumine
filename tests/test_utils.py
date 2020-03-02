import unittest
from unittest import mock

from flumine import utils


class UtilsTest(unittest.TestCase):
    def test_create_short_uuid(self):
        self.assertTrue(utils.create_short_uuid())

    def test_file_line_count(self):
        self.assertGreater(utils.file_line_count(__file__), 10)

    def test_keep_alive(self):
        mock_trading = mock.Mock()
        mock_trading.session_token = None
        utils.keep_alive(mock_trading, False)
        mock_trading.login.assert_called_with()

        utils.keep_alive(mock_trading, True)
        mock_trading.login_interactive.assert_called_with()

        mock_trading.session_token = 1
        mock_trading.session_expired = True
        utils.keep_alive(mock_trading, False)
        mock_trading.keep_alive.assert_called_with()
