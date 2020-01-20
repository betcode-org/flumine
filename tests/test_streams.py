import unittest
from unittest import mock

from flumine.streams import streams


class StreamsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.streams = streams.Streams()

    def test_init(self):
        self.assertEqual(self.streams._streams, [])
        self.assertEqual(self.streams._stream_id, 0)

    def test_call(self):
        pass

    def test_start(self):
        mock_stream = mock.Mock()
        self.streams._streams = [mock_stream]
        self.streams.start()
        mock_stream.start.assert_called()

    def test_stop(self):
        mock_stream = mock.Mock()
        self.streams._streams = [mock_stream]
        self.streams.stop()
        mock_stream.stop.assert_called()

    def test__increment_stream_id(self):
        self.assertEqual(self.streams._increment_stream_id(), 1000)

    def test_iter(self):
        for i in self.streams:
            assert i

    def test_len(self):
        self.assertEqual(len(self.streams), 0)
