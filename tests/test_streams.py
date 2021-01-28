import unittest
from unittest import mock

from flumine.streams import streams, datastream, historicalstream
from flumine.streams.basestream import BaseStream
from flumine.streams.simulatedorderstream import CurrentOrders
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
        mock_strategy = mock.Mock(streams=[], historic_stream_ids=[])
        mock_strategy.market_filter = {
            "markets": ["dubs of the mad skint and british"],
            "listener_kwargs": {"canary_yellow": True},
        }
        self.streams(mock_strategy)

        mock_add_historical_stream.assert_called_with(
            mock_strategy, "dubs of the mad skint and british", canary_yellow=True
        )
        self.assertEqual(len(mock_strategy.streams), 1)
        self.assertEqual(len(mock_strategy.historic_stream_ids), 1)

    def test_call_backtest_no_markets(self):
        self.mock_flumine.BACKTEST = True
        mock_strategy = mock.Mock()
        mock_strategy.streams = []
        mock_strategy.market_filter = {}
        self.streams(mock_strategy)
        self.assertEqual(len(mock_strategy.streams), 0)

    @mock.patch("flumine.streams.streams.Streams.add_order_stream")
    def test_add_client_betfair(self, mock_add_order_stream):
        mock_client = mock.Mock(order_stream=True, paper_trade=False)
        mock_client.EXCHANGE = streams.ExchangeType.BETFAIR
        self.streams.add_client(mock_client)
        mock_add_order_stream.assert_called_with(mock_client)

    @mock.patch("flumine.streams.streams.Streams.add_simulated_order_stream")
    def test_add_client_paper_trade(self, mock_add_simulated_order_stream):
        mock_client = mock.Mock(order_stream=True, paper_trade=True)
        mock_client.EXCHANGE = streams.ExchangeType.BETFAIR
        self.streams.add_client(mock_client)
        mock_add_simulated_order_stream.assert_called_with(mock_client)

    @mock.patch("flumine.streams.streams.Streams.add_order_stream")
    def test_add_client_no_order_stream(self, mock_add_order_stream):
        mock_client = mock.Mock(order_stream=False)
        mock_client.EXCHANGE = streams.ExchangeType.BETFAIR
        self.streams.add_client(mock_client)
        mock_add_order_stream.assert_not_called()

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

        self.streams.add_historical_stream(mock_strategy, "GANG", inplay=True)
        self.assertEqual(len(self.streams), 1)
        mock_increment.assert_called_with()
        mock_historical_stream_class.assert_called_with(
            flumine=self.mock_flumine,
            stream_id=mock_increment(),
            market_filter="GANG",
            market_data_filter=mock_strategy.market_data_filter,
            streaming_timeout=mock_strategy.streaming_timeout,
            conflate_ms=mock_strategy.conflate_ms,
            output_queue=False,
            inplay=True,
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

    @mock.patch("flumine.streams.streams.OrderStream")
    @mock.patch("flumine.streams.streams.Streams._increment_stream_id")
    def test_add_historical_stream_conflate(
        self, mock_increment, mock_order_stream_class
    ):
        conflate_ms = 500
        streaming_timeout = 0.5
        mock_client = mock.Mock()
        self.streams.add_order_stream(mock_client, conflate_ms, streaming_timeout)
        self.assertEqual(len(self.streams), 1)
        mock_increment.assert_called_with()
        mock_order_stream_class.assert_called_with(
            flumine=self.mock_flumine,
            stream_id=mock_increment(),
            streaming_timeout=streaming_timeout,
            conflate_ms=conflate_ms,
            client=mock_client,
        )

    @mock.patch("flumine.streams.streams.SimulatedOrderStream")
    @mock.patch("flumine.streams.streams.Streams._increment_stream_id")
    def test_add_simulated_order_stream(self, mock_increment, mock_order_stream_class):
        conflate_ms = 500
        streaming_timeout = 0.5
        mock_client = mock.Mock()
        self.streams.add_simulated_order_stream(
            mock_client, conflate_ms, streaming_timeout
        )
        self.assertEqual(len(self.streams), 1)
        mock_increment.assert_called_with()
        mock_order_stream_class.assert_called_with(
            flumine=self.mock_flumine,
            stream_id=mock_increment(),
            streaming_timeout=streaming_timeout,
            conflate_ms=conflate_ms,
            client=mock_client,
        )

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
        self.mock_client = mock.Mock()
        self.stream = BaseStream(
            self.mock_flumine,
            123,
            0.01,
            100,
            {"test": "me"},
            {"please": "now"},
            client=self.mock_client,
            output_queue=False,
            operation="test",
        )

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertEqual(self.stream.market_filter, {"test": "me"})
        self.assertEqual(self.stream.market_data_filter, {"please": "now"})
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)
        self.assertEqual(self.stream._client, self.mock_client)
        self.assertEqual(self.stream.MAX_LATENCY, 0.5)
        self.assertIsNone(self.stream._output_queue)
        self.assertEqual(self.stream.operation, "test")

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

    @mock.patch("flumine.streams.basestream.BaseStream.client")
    def test_betting_client(self, mock_client):
        self.assertEqual(self.stream.betting_client, mock_client.betting_client)

    def test_client(self):
        self.stream._client = 1
        self.assertEqual(self.stream.client, 1)
        self.stream._client = None
        self.assertEqual(self.stream.client, self.mock_flumine.client)


class TestMarketStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = streams.MarketStream(
            self.mock_flumine, 123, 0.01, 100, {"test": "me"}, {"please": "now"}
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
            self.mock_flumine, 123, 0.01, 100, {"test": "me"}, {"please": "now"}
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

    @mock.patch("flumine.streams.marketstream.BaseStream.betting_client")
    def test_run(self, mock_betting_client):
        self.stream.run()
        mock_betting_client.streaming.create_stream.assert_called_with(
            listener=self.stream._listener, unique_id=123
        )

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
        stream = datastream.FlumineStream(mock_listener, 0)
        self.assertEqual(str(stream), "FlumineStream")
        self.assertEqual(repr(stream), "<FlumineStream [0]>")

    def test_flumine_stream_on_process(self):
        mock_listener = mock.Mock()
        stream = datastream.FlumineStream(mock_listener, 0)
        stream.on_process([1, 2, 3])
        mock_listener.output_queue.put.called_with(datastream.RawDataEvent([1, 2, 3]))

    @mock.patch("flumine.streams.datastream.FlumineMarketStream.on_process")
    def test_flumine_market_stream(self, mock_on_process):
        mock_listener = mock.Mock(stream_unique_id=0)
        stream = datastream.FlumineMarketStream(mock_listener, 0)
        market_books = [{"id": "1.123"}, {"id": "1.456"}, {"id": "1.123"}]
        stream._process(market_books, 123)

        self.assertEqual(len(stream._caches), 2)
        self.assertEqual(stream._updates_processed, 3)
        mock_on_process.assert_called_with(
            [mock_listener.stream_unique_id, 123, market_books]
        )

    @mock.patch("flumine.streams.datastream.FlumineMarketStream.on_process")
    def test_flumine_market_stream_market_closed(self, mock_on_process):
        mock_listener = mock.Mock(stream_unique_id=0)
        stream = datastream.FlumineMarketStream(mock_listener, 0)
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
        mock_listener = mock.Mock(stream_unique_id=0)
        stream = datastream.FlumineRaceStream(mock_listener, 0)
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
            self.mock_flumine,
            123,
            0.01,
            100,
            {"test": "me"},
            {"please": "now"},
            inplay=True,
            seconds_to_start=123,
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
        self.assertTrue(self.stream._listener.inplay)
        self.assertEqual(self.stream._listener.seconds_to_start, 123)

    def test_run(self):
        self.stream.run()

    def test_handle_output(self):
        self.stream.handle_output()

    @mock.patch("flumine.streams.historicalstream.FlumineHistoricalGeneratorStream")
    def test_create_generator(self, mock_generator):
        generator = self.stream.create_generator()
        mock_generator.assert_called_with(
            file_path={"test": "me"},
            listener=self.stream._listener,
            operation="marketSubscription",
            unique_id=self.stream.stream_id,
        )
        self.assertIsNone(self.stream._listener.max_latency)
        self.assertFalse(self.stream._listener.lightweight)
        self.assertFalse(self.stream._listener.debug)
        self.assertFalse(self.stream._listener.update_clk)
        self.assertEqual(generator, mock_generator().get_generator())


class TestFlumineMarketStream(unittest.TestCase):
    def setUp(self) -> None:
        self.listener = mock.Mock()
        self.stream = historicalstream.FlumineMarketStream(self.listener, 0)

    def test_init(self):
        self.assertEqual(self.stream._listener, self.listener)
        self.assertEqual(self.stream._lookup, "mc")

    @mock.patch("flumine.streams.historicalstream.MarketBookCache")
    def test__process(self, mock_cache):
        self.assertFalse(
            self.stream._process(
                [{"id": "1.23", "img": {1: 2}, "marketDefinition": {"runners": []}}],
                12345,
            )
        )
        self.assertEqual(len(self.stream._caches), 1)
        self.assertEqual(self.stream._updates_processed, 1)
        mock_cache.assert_called_with("1.23", 12345, self.stream._listener.lightweight)
        mock_cache().update_cache.assert_called_with(
            {"id": "1.23", "img": {1: 2}, "marketDefinition": {"runners": []}}, 12345
        )

    def test_snap_inplay(self):
        # inPlay
        self.stream = historicalstream.FlumineMarketStream(
            mock.Mock(inplay=True, seconds_to_start=None), 0
        )
        self.stream._caches = {
            "1.123": mock.Mock(_definition_status="OPEN", _definition_in_play=False),
        }
        self.assertEqual(len(self.stream.snap()), 0)
        self.stream._caches = {
            "1.123": mock.Mock(_definition_status="OPEN", _definition_in_play=True),
        }
        self.assertEqual(len(self.stream.snap()), 1)
        self.stream._caches = {
            "1.123": mock.Mock(_definition_status="CLOSED", _definition_in_play=False),
        }
        self.assertEqual(len(self.stream.snap()), 1)

        self.stream = historicalstream.FlumineMarketStream(
            mock.Mock(inplay=False, seconds_to_start=None), 0
        )
        self.stream._caches = {
            "1.123": mock.Mock(_definition_status="OPEN", _definition_in_play=False),
        }
        self.assertEqual(len(self.stream.snap()), 1)
        self.stream._caches = {
            "1.123": mock.Mock(_definition_status="OPEN", _definition_in_play=True),
        }
        self.assertEqual(len(self.stream.snap()), 0)

    def test_snap_seconds_to_start(self):
        # secondsToStart
        self.stream = historicalstream.FlumineMarketStream(
            mock.Mock(inplay=None, seconds_to_start=600), 0
        )
        self.stream._caches = {
            "1.123": mock.Mock(
                publish_time=123,
                market_definition={
                    "status": "OPEN",
                    "inPlay": False,
                    "marketTime": 456,
                },
            )
        }
        self.assertEqual(len(self.stream.snap()), 1)
        self.stream._caches = {
            "1.123": mock.Mock(
                publish_time=123,
                market_definition={
                    "status": "OPEN",
                    "inPlay": False,
                    "marketTime": 1234567,
                },
            )
        }
        self.assertEqual(len(self.stream.snap()), 0)


class TestFlumineRaceStream(unittest.TestCase):
    def setUp(self) -> None:
        self.listener = mock.Mock()
        self.stream = historicalstream.FlumineRaceStream(self.listener, 0)

    @mock.patch("flumine.streams.historicalstream.RaceCache")
    def test__process(self, mock_cache):
        self.assertFalse(
            self.stream._process(
                [{"mid": "1.23", "id": 1, "img": {1: 2}}],
                12345,
            )
        )
        self.assertEqual(len(self.stream._caches), 1)
        self.assertEqual(self.stream._updates_processed, 1)
        mock_cache.assert_called_with(
            "1.23", 12345, 1, self.stream._listener.lightweight
        )
        mock_cache().update_cache.assert_called_with(
            {"mid": "1.23", "id": 1, "img": {1: 2}}, 12345
        )


class TestHistoricListener(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.listener = historicalstream.HistoricListener(
            inplay=True, seconds_to_start=123
        )

    def test_init(self):
        self.assertTrue(self.listener.inplay)
        self.assertEqual(self.listener.seconds_to_start, 123)

    @mock.patch("flumine.streams.historicalstream.FlumineMarketStream")
    def test__add_stream_market(self, mock_stream):
        self.assertEqual(
            self.listener._add_stream(123, "marketSubscription"), mock_stream()
        )

    def test__add_stream_order(self):
        with self.assertRaises(ListenerError):
            self.listener._add_stream(123, "orderSubscription")

    @mock.patch("flumine.streams.historicalstream.FlumineRaceStream")
    def test__add_stream_race(self, mock_stream):
        self.assertEqual(
            self.listener._add_stream(123, "raceSubscription"), mock_stream()
        )

    def test_on_data(self):
        mock_stream = mock.Mock(_lookup="mc")
        self.listener.stream = mock_stream
        self.listener.on_data('{"pt": 123, "mc": {}}')
        self.listener.stream._process.assert_called_with({}, 123)
        # error
        self.assertIsNone(self.listener.on_data("p"))


class TestOrderStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = streams.OrderStream(self.mock_flumine, 123, 0.01, 100)

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertIsNone(self.stream.market_filter)
        self.assertIsNone(self.stream.market_data_filter)
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)

    # def test_run(self):
    #     pass
    #
    # def test_handle_output(self):
    #     pass


class TestSimulatedOrderStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = streams.SimulatedOrderStream(self.mock_flumine, 123, 0.01, 100)

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertIsNone(self.stream.market_filter)
        self.assertIsNone(self.stream.market_data_filter)
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)

    def test_current_orders(self):
        current_orders = CurrentOrders([1])
        self.assertEqual(current_orders.orders, [1])
        self.assertFalse(current_orders.more_available)

    # def test_run(self):
    #     pass

    def test__get_current_orders(self):
        mock_market = mock.Mock(closed=False)
        order_one = mock.Mock(simulated=True)
        order_one.trade.client = self.stream.client
        order_two = mock.Mock(simulated=True)
        order_three = mock.Mock(simulated=True)
        mock_market.blotter = [order_one, order_two, order_three]
        self.stream.flumine.markets = [mock_market, mock.Mock(closed=True)]
        self.assertEqual(self.stream._get_current_orders(), [order_one])
