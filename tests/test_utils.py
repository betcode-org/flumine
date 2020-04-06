import unittest
from unittest import mock

from flumine import utils


class UtilsTest(unittest.TestCase):
    def test_create_short_uuid(self):
        self.assertTrue(utils.create_short_uuid())

    def test_file_line_count(self):
        self.assertGreater(utils.file_line_count(__file__), 10)

    def test_keep_alive(self):
        mock_client = mock.Mock()
        mock_client.betting_client.session_token = None
        utils.keep_alive(mock_client)
        mock_client.login.assert_called_with()

        mock_client.betting_client.session_token = 1
        mock_client.betting_client.session_expired = True
        utils.keep_alive(mock_client)
        mock_client.keep_alive.assert_called_with()
