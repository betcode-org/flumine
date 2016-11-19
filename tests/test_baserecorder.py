import unittest
from unittest import mock

from flumine.resources.baserecorder import BaseRecorder


class BaseRecorderTest(unittest.TestCase):

    def setUp(self):
        self.market_filter = mock.Mock()
        self.market_data_filter = mock.Mock()
        self.base_recorder = BaseRecorder(self.market_filter, self.market_data_filter)

    def test_init(self):
        assert self.base_recorder.name == 'BASE_RECORDER'
        assert self.base_recorder._market_filter == self.market_filter
        assert self.base_recorder._market_data_filter == self.market_data_filter

    @mock.patch('flumine.resources.baserecorder.BaseRecorder.process_market_book')
    @mock.patch('flumine.resources.baserecorder.BaseRecorder.market_book_parameters')
    def test_call(self, mock_market_book_parameters, mock_process_market_book):
        mock_market_book = mock.Mock()
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

    def test_market_filter(self):
        assert self.base_recorder.market_filter == self.market_filter.serialise

    def test_market_data_filter(self):
        assert self.base_recorder.market_data_filter == self.market_data_filter.serialise

    def test_str(self):
        assert str(self.base_recorder) == '<BASE_RECORDER>'
