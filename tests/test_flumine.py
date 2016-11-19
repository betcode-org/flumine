import unittest
from unittest import mock

from flumine.flumine import Flumine


class FlumineTest(unittest.TestCase):

    def setUp(self):
        self.trading = mock.Mock()
        self.recorder = mock.Mock()
        self.flumine = Flumine(self.trading, self.recorder)
        self.listener = mock.Mock()
        self.flumine._listener = self.listener

    def test_init(self):
        assert self.flumine.trading == self.trading
        assert self.flumine.recorder == self.recorder
        assert self.flumine._socket is None
        assert self.flumine._running is False
        assert self.flumine._listener is not None

    @mock.patch('flumine.flumine.Flumine._create_socket')
    @mock.patch('flumine.flumine.Flumine._check_login')
    def test_start(self, mock_check_login, mock_create_socket):
        mock_socket = mock.Mock()
        self.flumine._socket = mock_socket

        self.flumine.start()

        mock_check_login.assert_called_with()
        mock_create_socket.assert_called_with()
        mock_socket.subscribe_to_markets.assert_called_with(
                unique_id=2,
                market_filter=self.recorder.market_filter,
                market_data_filter=self.recorder.market_data_filter
        )
        mock_socket.start.assert_called_with(async=True)
        assert self.flumine._running is True

    def test_stop(self):
        self.flumine._socket = mock.Mock()
        self.flumine.stop()

        self.flumine._socket.stop.assert_called_with()
        assert self.flumine._running is False

    def test_check_login(self):
        self.trading.session_expired.return_value = True

        self.flumine._check_login()
        self.trading.login.assert_called_with()

    def test_create_socket(self):
        self.flumine._create_socket()

        self.flumine.trading.streaming.create_stream.assert_called_with(
                description='Flumine Socket',
                unique_id=1,
                listener=self.listener
        )

    def test_stream_status(self):
        self.flumine._socket = mock.Mock()
        socket_str = mock.Mock()
        socket_str.return_value = '123'
        self.flumine._socket.__str__ = socket_str

        assert self.flumine.stream_status() == '123'

    def test_str(self):
        assert str(self.flumine) == '<Flumine [not running]>'
