import unittest
from unittest import mock

from flumine.flumine import Flumine
from flumine.exceptions import RunError
from betfairlightweight import BetfairError


class FlumineTest(unittest.TestCase):

    def setUp(self):
        self.settings = {'betfairlightweight': {'username': 'username'}}
        self.recorder = mock.Mock()
        self.mock_client = mock.Mock()
        Flumine._create_client = self.mock_client
        self.flumine = Flumine(self.recorder, settings=self.settings)
        self.listener = mock.Mock()
        self.flumine.listener = self.listener

    def test_init(self):
        assert self.flumine.trading == self.mock_client()
        assert self.flumine.recorder == self.recorder
        assert self.flumine._socket is None
        assert self.flumine._running is False
        assert self.flumine.listener is not None

    @mock.patch('flumine.flumine.Flumine._run')
    def test_start(self, mock_run):
        mock_socket = mock.Mock()
        handler_thread = mock.Mock()
        run_thread = mock.Mock()

        self.flumine._socket = mock_socket
        self.flumine._handler_thread = handler_thread
        self.flumine._run_thread = run_thread

        self.flumine.start()

        mock_run.assert_called_with(None, None, None)

    def test_start_running(self):
        self.flumine._running = True
        with self.assertRaises(RunError):
            self.flumine.start()

    def test_stop(self):
        self.flumine._socket = mock.Mock()
        self.flumine._running = True
        self.flumine.stop()

        assert self.flumine._running is False
        assert self.flumine._socket is None

    def test_stop_error(self):
        with self.assertRaises(RunError):
            self.flumine.stop()

    @mock.patch('flumine.flumine.APIClient')
    def test_create_client(self, mock_api_client):
        settings = {'betfairlightweight': {'username': 'username'}}
        client = self.flumine._create_client(settings)

        assert client == self.mock_client()

    # def test_run(self):
    #     socket = mock.Mock()
    #     self.flumine._socket = socket
    #     self.flumine._running = True
    #     self.flumine._run()
    #
    #     socket.start.assert_called_with(async=False)
    # mock_socket.subscribe_to_markets.assert_called_with(
    #     market_filter=self.recorder.market_filter,
    #     market_data_filter=self.recorder.market_data_filter,
    #     conflate_ms=None,
    #     heartbeat_ms=None,
    #     segmentation_enabled=None,
    # )
    #
    #     socket.start.side_effect = BetfairError()
    #     self.flumine._run()

    def test_check_login(self):
        mock_client = mock.Mock()
        mock_client.session_expired = True
        self.flumine.trading = mock_client

        self.flumine._check_login()
        mock_client.login.assert_called_with()

    def test_create_socket(self):
        self.flumine._create_socket()

        self.flumine.trading.streaming.create_stream.assert_called_with(
                description='Flumine Socket',
                unique_id=1000,
                listener=self.listener
        )

    def test_stream_status(self):
        assert self.flumine.stream_status() == 'Socket not created'

        self.flumine._socket = mock.Mock()
        socket_str = mock.Mock()
        socket_str.return_value = '123'
        self.flumine._socket.__str__ = socket_str

        assert self.flumine.stream_status() == '123'

    def test_running(self):
        self.flumine._running = True
        assert self.flumine.running is True

        self.flumine._running = False
        assert self.flumine.running is False

    def test_str(self):
        assert str(self.flumine) == '<Flumine [not running]>'

    def test_repr(self):
        assert repr(self.flumine) == '<Flumine>'
