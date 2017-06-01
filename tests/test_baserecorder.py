import unittest
from unittest import mock

from flumine.resources.recorder import BaseRecorder, StreamRecorder


class BaseRecorderTest(unittest.TestCase):

    def setUp(self):
        self.storage = mock.Mock()
        self.mock_market_filter = mock.Mock()
        self.mock_market_data_filter = mock.Mock()
        self.base_recorder = BaseRecorder(self.storage, self.mock_market_filter, self.mock_market_data_filter)

    def test_init(self):
        assert self.base_recorder.NAME == 'BASE_RECORDER'
        assert self.base_recorder.storage_engine == self.storage
        assert self.base_recorder.market_filter == self.mock_market_filter
        assert self.base_recorder.market_data_filter == self.mock_market_data_filter

    @mock.patch('flumine.resources.recorder.BaseRecorder.process_market_book')
    @mock.patch('flumine.resources.recorder.BaseRecorder.market_book_parameters')
    def test_call(self, mock_market_book_parameters, mock_process_market_book):
        mock_market_book = mock.Mock()
        mock_market_book.status = 'OPEN'
        self.base_recorder(mock_market_book)

        mock_market_book_parameters.assert_called_with(mock_market_book)
        mock_process_market_book.assert_called_with(mock_market_book)

    def test_market_book_parameters(self):
        mock_market_book = mock.Mock()
        assert self.base_recorder.market_book_parameters(mock_market_book) is True

    def test_process_market_book(self):
        with self.assertRaises(NotImplementedError):
            mock_market_book = mock.Mock()
            self.base_recorder.process_market_book(mock_market_book)

    # def test_on_market_closed(self):
    #     self.base_recorder.on_market_closed(None)

    def test_str(self):
        assert str(self.base_recorder) == '<BASE_RECORDER>'


class StreamRecorderTest(unittest.TestCase):

    def setUp(self):
        self.storage = mock.Mock()
        self.mock_market_filter = mock.Mock()
        self.mock_market_data_filter = mock.Mock()
        self.in_play = True
        self.data_recorder = StreamRecorder(
            self.storage, self.mock_market_filter, self.mock_market_data_filter
        )

    def test_init(self):
        assert self.data_recorder.NAME == 'STREAM_RECORDER'
        assert self.data_recorder.storage_engine == self.storage
        assert self.data_recorder.market_filter == self.mock_market_filter
        assert self.data_recorder.market_data_filter == self.mock_market_data_filter

    def test_market_parameters(self):
        market_book = mock.Mock()
        market_book.status = 'OPEN'
        market_book.inplay = True

        assert self.data_recorder.market_book_parameters(market_book) is True
