import unittest
from unittest import mock

from flumine.flumine import Flumine


class FlumineTest(unittest.TestCase):

    def setUp(self):
        self.trading = mock.Mock()
        self.strategies = mock.Mock()
        self.flumine = Flumine(self.trading, self.strategies)

    def test_init(self):
        assert self.flumine.trading == self.trading
        assert self.flumine.strategies == self.strategies

    @mock.patch('flumine.flumine.Flumine._create_socket')
    @mock.patch('flumine.flumine.Flumine._check_login')
    def test_start(self, mock_check_login, mock_create_socket):
        market_filter = mock.Mock()
        market_data_filter = mock.Mock()
        mock_socket = mock.Mock()
        self.flumine._socket = mock_socket

        self.flumine.start(market_filter, market_data_filter)

        mock_check_login.assert_called_with()
        mock_create_socket.assert_called_with()
        mock_socket.subscribe_to_markets.assert_called_with(
                unique_id=2,
                market_filter=market_filter,
                market_data_filter=market_data_filter
        )
        mock_socket.start.assert_called_with(async=True)

    def test_stop(self):
        self.flumine._socket = mock.Mock()
        self.flumine.stop()

        self.flumine._socket.stop.assert_called_with()

    def test_check_login(self):
        self.trading.session_expired.return_value = True

        self.flumine._check_login()
        self.trading.login.assert_called_with()

    def test_create_socket(self):
        self.flumine._create_socket()

        self.flumine.trading.streaming.create_stream.assert_called_with(
                description='Flumine Socket',
                unique_id=1
        )

    def test_str(self):
        assert str(self.flumine) == '<Flumine>'
