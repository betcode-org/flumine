import unittest
from unittest import mock

from flumine.streams import streams, datastream
from flumine.streams.basestream import BaseStream
from flumine.exceptions import ListenerError


class StreamsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.mock_flumine.BACKTEST = False
        self.streams = streams.Streams(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.streams.flumine, self.mock_flumine)
        self.assertEqual(self.streams._streams, [])
        self.assertEqual(self.streams._stream_id, 0)

    @mock.patch("flumine.streams.streams.Streams.add_stream")
    def test_call(self, mock_add_stream):
        mock_strategy = mock.Mock()
        mock_strategy.streams = []
        mock_strategy.raw_data = False
        self.streams(mock_strategy)

        mock_add_stream.assert_called_with(mock_strategy)
        self.assertEqual(len(mock_strategy.streams), 1)

    @mock.patch("flumine.streams.streams.Streams.add_stream")
    def test_call_data_stream(self, mock_add_stream):
        mock_strategy = mock.Mock()
        mock_strategy.streams = []
        mock_strategy.stream_class = datastream.DataStream
        self.streams(mock_strategy)

        mock_add_stream.assert_called_with(mock_strategy)
        self.assertEqual(len(mock_strategy.streams), 1)

    @mock.patch("flumine.streams.streams.Streams.add_historical_stream")
    def test_call_backtest(self, mock_add_historical_stream):
        self.mock_flumine.BACKTEST = True
        mock_strategy = mock.Mock()
        mock_strategy.streams = []
        mock_strategy.market_filter = {"markets": ["dubs of the mad skint and british"]}
        self.streams(mock_strategy)

        mock_add_historical_stream.assert_called_with(
            mock_strategy, "dubs of the mad skint and british"
        )
        self.assertEqual(len(mock_strategy.streams), 1)

    def test_call_backtest_no_markets(self):
        self.mock_flumine.BACKTEST = True
        mock_strategy = mock.Mock()
        mock_strategy.streams = []
        mock_strategy.market_filter = {}
        self.streams(mock_strategy)
        self.assertEqual(len(mock_strategy.streams), 0)

    @mock.patch("flumine.streams.streams.Streams._increment_stream_id")
    def test_add_stream_new(self, mock_increment):
        mock_strategy = mock.Mock()
        mock_stream_class = mock.Mock()
        mock_strategy.stream_class = mock_stream_class

        self.streams.add_stream(mock_strategy)
        self.assertEqual(len(self.streams), 1)
        mock_increment.assert_called_with()
        mock_strategy.stream_class.assert_called_with(
            flumine=self.mock_flumine,
            stream_id=mock_increment(),
            market_filter=mock_strategy.market_filter,
            market_data_filter=mock_strategy.market_data_filter,
            streaming_timeout=mock_strategy.streaming_timeout,
            conflate_ms=mock_strategy.conflate_ms,
        )

    @mock.patch("flumine.streams.streams.Streams._increment_stream_id")
    def test_add_stream_old(self, mock_increment):
        mock_strategy = mock.Mock()
        mock_strategy.market_filter = 1
        mock_strategy.market_data_filter = 2
        mock_strategy.streaming_timeout = 3
        mock_strategy.conflate_ms = 4
        mock_strategy.stream_class = streams.MarketStream

        stream = mock.Mock(spec=streams.MarketStream)
        stream.market_filter = 1
        stream.market_data_filter = 2
        stream.streaming_timeout = 3
        stream.conflate_ms = 4
        stream.stream_id = 1001
        self.streams._streams = [stream]

        new_stream = self.streams.add_stream(mock_strategy)
        self.assertEqual(len(self.streams), 1)
        self.assertEqual(stream, new_stream)
        mock_increment.assert_not_called()

    @mock.patch("flumine.streams.streams.HistoricalStream")
    @mock.patch("flumine.streams.streams.Streams._increment_stream_id")
    def test_add_historical_stream(self, mock_increment, mock_historical_stream_class):
        self.mock_flumine.BACKTEST = True
        mock_strategy = mock.Mock()
        mock_strategy.market_filter = 1
        mock_strategy.market_data_filter = 2
        mock_strategy.streaming_timeout = 3
        mock_strategy.conflate_ms = 4
        mock_strategy.stream_class = streams.MarketStream

        self.streams.add_historical_stream(mock_strategy, "GANG")
        self.assertEqual(len(self.streams), 1)
        mock_increment.assert_called_with()
        mock_historical_stream_class.assert_called_with(
            flumine=self.mock_flumine,
            stream_id=mock_increment(),
            market_filter="GANG",
            market_data_filter=mock_strategy.market_data_filter,
            streaming_timeout=mock_strategy.streaming_timeout,
            conflate_ms=mock_strategy.conflate_ms,
        )

    def test_add_historical_stream_old(self):
        self.mock_flumine.BACKTEST = True
        mock_strategy = mock.Mock()
        mock_stream = mock.Mock(spec=streams.HistoricalStream)
        mock_stream.market_filter = "GANG"
        self.streams._streams = [mock_stream]

        stream = self.streams.add_historical_stream(mock_strategy, "GANG")
        self.assertEqual(stream, mock_stream)
        self.assertEqual(len(self.streams), 1)

    def test_start(self):
        mock_stream = mock.Mock()
        self.streams._streams = [mock_stream]
        self.streams.start()
        mock_stream.start.assert_called_with()

    def test_start_backtest(self):
        self.mock_flumine.BACKTEST = True
        mock_stream = mock.Mock()
        self.streams._streams = [mock_stream]
        self.streams.start()
        mock_stream.start.assert_not_called()

    def test_stop(self):
        mock_stream = mock.Mock()
        self.streams._streams = [mock_stream]
        self.streams.stop()
        mock_stream.stop.assert_called_with()

    def test__increment_stream_id(self):
        self.assertEqual(self.streams._increment_stream_id(), 1000)

    def test_iter(self):
        for i in self.streams:
            assert i

    def test_len(self):
        self.assertEqual(len(self.streams), 0)


class TestBaseStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = BaseStream(
            self.mock_flumine, 123, {"test": "me"}, {"please": "now"}, 0.01, 100
        )

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertEqual(self.stream.market_filter, {"test": "me"})
        self.assertEqual(self.stream.market_data_filter, {"please": "now"})
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)
        self.assertEqual(self.stream.MAX_LATENCY, 0.5)

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.stream.run()

    def test_handle_output(self):
        with self.assertRaises(NotImplementedError):
            self.stream.handle_output()

    def test_stop(self):
        mock_stream = mock.Mock()
        self.stream._stream = mock_stream
        self.stream.stop()
        mock_stream.stop.assert_called_with()

    def test_trading(self):
        self.assertEqual(
            self.stream.betting_client, self.mock_flumine.client.betting_client
        )


class TestMarketStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = streams.MarketStream(
            self.mock_flumine, 123, {"test": "me"}, {"please": "now"}, 0.01, 100
        )

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertEqual(self.stream.market_filter, {"test": "me"})
        self.assertEqual(self.stream.market_data_filter, {"please": "now"})
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)

    # def test_run(self):
    #     pass
    #
    # def test_handle_output(self):
    #     pass


class TestDataStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = streams.DataStream(
            self.mock_flumine, 123, {"test": "me"}, {"please": "now"}, 0.01, 100
        )

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertEqual(self.stream.market_filter, {"test": "me"})
        self.assertEqual(self.stream.market_data_filter, {"please": "now"})
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)
        self.assertEqual(self.stream.LISTENER, datastream.FlumineListener)
        self.assertEqual(
            self.stream._listener.output_queue, self.mock_flumine.handler_queue
        )

    # def test_run(self):
    #     pass
    #
    # def test_handle_output(self):
    #     pass

    @mock.patch("flumine.streams.datastream.FlumineRaceStream")
    @mock.patch("flumine.streams.datastream.FlumineMarketStream")
    def test_flumine_listener(self, mock_market_stream, mock_race_stream):
        listener = datastream.FlumineListener()
        self.assertEqual(
            listener._add_stream(123, "marketSubscription"), mock_market_stream()
        )

        with self.assertRaises(ListenerError):
            listener._add_stream(123, "orderSubscription")

        listener = datastream.FlumineListener()
        self.assertEqual(
            listener._add_stream(123, "raceSubscription"), mock_race_stream()
        )

    def test_flumine_stream(self):
        mock_listener = mock.Mock()
        stream = datastream.FlumineStream(mock_listener)
        self.assertEqual(str(stream), "FlumineStream")
        self.assertEqual(repr(stream), "<FlumineStream [0]>")

    def test_flumine_stream_on_process(self):
        mock_listener = mock.Mock()
        stream = datastream.FlumineStream(mock_listener)
        stream.on_process([1, 2, 3])
        mock_listener.output_queue.put.called_with(datastream.RawDataEvent([1, 2, 3]))

    @mock.patch("flumine.streams.datastream.FlumineMarketStream.on_process")
    def test_flumine_market_stream(self, mock_on_process):
        mock_listener = mock.Mock()
        stream = datastream.FlumineMarketStream(mock_listener)
        market_books = [{"id": "1.123"}, {"id": "1.456"}, {"id": "1.123"}]
        stream._process(market_books, 123)

        self.assertEqual(len(stream._caches), 2)
        self.assertEqual(stream._updates_processed, 3)
        mock_on_process.assert_called_with(
            [mock_listener.stream_unique_id, 123, market_books]
        )

    @mock.patch("flumine.streams.datastream.FlumineMarketStream.on_process")
    def test_flumine_market_stream_market_closed(self, mock_on_process):
        mock_listener = mock.Mock()
        stream = datastream.FlumineMarketStream(mock_listener)
        stream._caches = {"1.123": object}
        market_books = [{"id": "1.123", "marketDefinition": {"status": "CLOSED"}}]
        stream._process(market_books, 123)

        self.assertEqual(stream._lookup, "mc")
        self.assertEqual(len(stream._caches), 0)
        self.assertEqual(stream._updates_processed, 1)
        mock_on_process.assert_called_with(
            [mock_listener.stream_unique_id, 123, market_books]
        )

    @mock.patch("flumine.streams.datastream.FlumineRaceStream.on_process")
    def test_flumine_race_stream(self, mock_on_process):
        mock_listener = mock.Mock()
        stream = datastream.FlumineRaceStream(mock_listener)
        race_updates = [{"mid": "1.123"}, {"mid": "1.456"}, {"mid": "1.123"}]
        stream._process(race_updates, 123)

        self.assertEqual(stream._lookup, "rc")
        self.assertEqual(len(stream._caches), 2)
        self.assertEqual(stream._updates_processed, 3)
        mock_on_process.assert_called_with(
            [mock_listener.stream_unique_id, 123, race_updates]
        )


class TestHistoricalStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = streams.HistoricalStream(
            self.mock_flumine, 123, {"test": "me"}, {"please": "now"}, 0.01, 100
        )

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertEqual(self.stream.market_filter, {"test": "me"})
        self.assertEqual(self.stream.market_data_filter, {"please": "now"})
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)
        self.assertIsNone(self.stream.MAX_LATENCY)

    def test_run(self):
        self.stream.run()

    def test_handle_output(self):
        self.stream.handle_output()

    @mock.patch("flumine.streams.historicalstream.HistoricalGeneratorStream")
    def test_create_generator(self, mock_generator):
        self.assertEqual(
            self.stream.create_generator(), mock_generator().get_generator()
        )
