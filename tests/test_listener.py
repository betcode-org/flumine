import unittest
from unittest import mock

from flumine.listener import (
    FlumineListener,
    FlumineStream,
    FlumineRaceStream,
)
from flumine.exceptions import ListenerError


class ListenerTest(unittest.TestCase):

    def setUp(self):
        self.mock_recorder = mock.Mock()
        self.listener = FlumineListener(self.mock_recorder)

    def test_init(self):
        assert self.listener.recorder == self.mock_recorder

    @mock.patch('flumine.listener.FlumineStream')
    def test_add_stream(self, mock_flumine_stream):
        self.listener._add_stream(1, 'marketSubscription')
        mock_flumine_stream.assert_called_with(self.listener)

    def test_add_stream_error(self):
        with self.assertRaises(ListenerError):
            self.listener._add_stream(1, 'orderSubscription')


class StreamTest(unittest.TestCase):

    def setUp(self):
        self.mock_listener = mock.Mock()
        self.stream = FlumineStream(self.mock_listener)

    @mock.patch('flumine.listener.FlumineStream.output_queue')
    def test_process(self, mock_output_queue):
        market_book = {'id': 1}
        market_books = [market_book]

        self.stream._process(market_books, 1234)

        mock_output_queue.assert_called_with(market_books, 1234)
        assert len(self.stream._caches) == 1
        assert self.stream._updates_processed == 1

    @mock.patch('flumine.listener.FlumineStream.output_queue')
    def test_process_closed(self, mock_output_queue):
        self.stream._caches = {1: object()}
        market_book = {'id': 1, 'marketDefinition': {'status': 'CLOSED'}}
        market_books = [market_book]

        self.stream._process(market_books, 1234)

        mock_output_queue.assert_called_with(market_books, 1234)
        assert len(self.stream._caches) == 0
        assert self.stream._updates_processed == 1

    def test_str(self):
        assert str(self.stream) == 'FlumineStream'

    def test_repr(self):
        assert repr(self.stream) == '<FlumineStream [0]>'


class RaceTest(unittest.TestCase):

    def setUp(self):
        self.mock_listener = mock.Mock()
        self.stream = FlumineRaceStream(self.mock_listener)

    @mock.patch('flumine.listener.FlumineRaceStream.output_queue')
    def test_process(self, mock_output_queue):
        race = {'mid': 1}
        race_updates = [race]

        self.stream._process(race_updates, 1234)

        mock_output_queue.assert_called_with(race_updates, 1234)
        assert len(self.stream._caches) == 1
        assert self.stream._updates_processed == 1

    def test_str(self):
        assert str(self.stream) == 'FlumineRaceStream'

    def test_repr(self):
        assert repr(self.stream) == '<FlumineRaceStream [0]>'
