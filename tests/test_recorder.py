import unittest
from unittest import mock

from flumine.resources.recorder import BaseRecorder, MarketRecorder, RaceRecorder


class BaseRecorderTest(unittest.TestCase):
    @mock.patch("flumine.resources.recorder.os.makedirs")
    def setUp(self, *args):
        self.storage = mock.Mock()
        self.mock_market_filter = mock.Mock()
        self.mock_market_data_filter = mock.Mock()
        self.base_recorder = BaseRecorder(
            self.storage, self.mock_market_filter, self.mock_market_data_filter
        )

    def test_init(self):
        assert self.base_recorder.NAME == "BASE_RECORDER"
        assert self.base_recorder.STREAM_TYPE is None
        assert self.base_recorder.MARKET_ID_LOOKUP is None
        assert self.base_recorder.HOST is None
        assert self.base_recorder.storage_engine == self.storage
        assert self.base_recorder.market_filter == self.mock_market_filter
        assert self.base_recorder.market_data_filter == self.mock_market_data_filter
        assert self.base_recorder.stream_id is not None
        assert self.base_recorder.live_markets == []
        assert self.base_recorder.local_dir == "/tmp"

    @mock.patch("flumine.resources.recorder.BaseRecorder.process_update")
    @mock.patch("flumine.resources.recorder.BaseRecorder.check_market_book")
    def test_call(self, mock_check_market_book, mock_process_market_book):
        mock_market_book = mock.Mock()
        mock_market_book.status = "OPEN"
        mock_market_book.__get__ = "1.123"
        self.base_recorder.live_markets = [mock_market_book.get("id")]
        self.base_recorder([mock_market_book], 0)

        mock_check_market_book.assert_called_with(
            mock_market_book.get("id"), mock_market_book
        )
        mock_process_market_book.assert_called_with(mock_market_book, 0)

    def test_check_market_book(self):
        mock_market_book = mock.Mock()
        assert self.base_recorder.check_market_book("1.123", mock_market_book) is None
        assert self.base_recorder.live_markets == ["1.123"]

    def test_process_updatek(self):
        with self.assertRaises(NotImplementedError):
            mock_market_book = mock.Mock()
            self.base_recorder.process_update(mock_market_book, 0)

    def test_on_market_closed(self):
        mock_update = mock.Mock()
        self.base_recorder.on_market_closed(mock_update)

        self.storage.assert_called_with(
            mock_update.get(None),
            mock_update.get("marketDefinition"),
            self.base_recorder.stream_id,
        )

    def test_str(self):
        assert str(self.base_recorder) == "<BASE_RECORDER>"


class MarketRecorderTest(unittest.TestCase):
    @mock.patch("flumine.resources.recorder.os.makedirs")
    def setUp(self, *args):
        self.storage = mock.Mock()
        self.mock_market_filter = mock.Mock()
        self.mock_market_data_filter = mock.Mock()
        self.data_recorder = MarketRecorder(
            self.storage, self.mock_market_filter, self.mock_market_data_filter
        )

    def test_init(self):
        assert self.data_recorder.NAME == "MARKET_RECORDER"
        assert self.data_recorder.STREAM_TYPE == "market"
        assert self.data_recorder.MARKET_ID_LOOKUP == "id"
        assert self.data_recorder.storage_engine == self.storage
        assert self.data_recorder.market_filter == self.mock_market_filter
        assert self.data_recorder.market_data_filter == self.mock_market_data_filter


class RaceRecorderTest(unittest.TestCase):
    @mock.patch("flumine.resources.recorder.os.makedirs")
    def setUp(self, *args):
        self.storage = mock.Mock()
        self.data_recorder = RaceRecorder(self.storage)

    def test_init(self):
        assert self.data_recorder.NAME == "RACE_RECORDER"
        assert self.data_recorder.STREAM_TYPE == "race"
        assert self.data_recorder.MARKET_ID_LOOKUP == "mid"
        assert self.data_recorder.HOST == "race"
        assert self.data_recorder.storage_engine == self.storage
