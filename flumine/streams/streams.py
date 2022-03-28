import time
import logging
from typing import Union, Iterator

from ..strategy.strategy import BaseStrategy
from .marketstream import MarketStream
from .sportsdatastream import SportsDataStream
from .datastream import DataStream
from .historicalstream import HistoricalStream
from .orderstream import OrderStream
from .simulatedorderstream import SimulatedOrderStream
from ..clients import ExchangeType, BaseClient
from ..utils import get_file_md

logger = logging.getLogger(__name__)


class Streams:
    def __init__(self, flumine):
        self.flumine = flumine
        self._streams = []
        self._stream_id = 0

    def __call__(self, strategy: BaseStrategy) -> None:
        if self.flumine.SIMULATED:
            markets = strategy.market_filter.get("markets")
            market_types = strategy.market_filter.get("market_types")
            country_codes = strategy.market_filter.get("country_codes")
            event_processing = strategy.market_filter.get("event_processing", False)
            events = strategy.market_filter.get("events")
            listener_kwargs = strategy.market_filter.get("listener_kwargs", {})
            if markets and events:
                logger.warning(
                    "Markets and events found for strategy {0} skipping as flumine can only handle one type".format(
                        strategy
                    )
                )
            elif markets is None and events is None:
                logger.warning(
                    "No markets or events found for strategy {0}".format(strategy)
                )
            elif markets:
                # order markets by name as an attempt to process in chronological order
                markets.sort()
                for market in markets:
                    market_type = get_file_md(market, "marketType")
                    country_code = get_file_md(market, "countryCode")
                    if market_types and market_type and market_type not in market_types:
                        logger.warning(
                            "Skipping market %s (%s) for strategy %s due to marketType filter"
                            % (market, market_type, strategy)
                        )
                    elif (
                        country_codes
                        and country_code
                        and country_code not in country_codes
                    ):
                        logger.warning(
                            "Skipping market %s (%s) for strategy %s due to countryCode filter"
                            % (market, country_code, strategy)
                        )
                    else:
                        stream = self.add_historical_stream(
                            strategy, market, event_processing, **listener_kwargs
                        )
                        strategy.streams.append(stream)
                        strategy.historic_stream_ids.append(stream.stream_id)
            elif events:
                raise NotImplementedError()
        else:
            self.add_stream(strategy)

    def add_client(self, client: BaseClient) -> None:
        if client.order_stream:
            if client.paper_trade:
                self.add_simulated_order_stream(client)
            elif client.EXCHANGE == ExchangeType.BETFAIR:
                self.add_order_stream(client)

    """ market data """

    def add_stream(self, strategy: BaseStrategy) -> None:
        # markets
        if isinstance(strategy.market_filter, dict) or strategy.market_filter is None:
            market_filters = [strategy.market_filter]
        else:
            market_filters = strategy.market_filter
        for market_filter in market_filters:
            for stream in self:  # check if market stream already exists
                if (
                    isinstance(stream, strategy.stream_class)
                    and stream.market_filter == market_filter
                    and stream.market_data_filter == strategy.market_data_filter
                    and stream.streaming_timeout == strategy.streaming_timeout
                    and stream.conflate_ms == strategy.conflate_ms
                ):
                    logger.info(
                        "Using {0} ({1}) for strategy {2}".format(
                            strategy.stream_class, stream.stream_id, strategy
                        )
                    )
                    strategy.streams.append(stream)
                    break
            else:  # nope? lets create a new one
                stream_id = self._increment_stream_id()
                logger.info(
                    "Creating new {0} ({1}) for strategy {2}".format(
                        strategy.stream_class, stream_id, strategy
                    )
                )
                stream = strategy.stream_class(
                    flumine=self.flumine,
                    stream_id=stream_id,
                    market_filter=market_filter,
                    market_data_filter=strategy.market_data_filter,
                    streaming_timeout=strategy.streaming_timeout,
                    conflate_ms=strategy.conflate_ms,
                )
                self._streams.append(stream)
                strategy.streams.append(stream)
        # sports data
        for subscription in strategy.sports_data_filter:
            for stream in self:  # check if sports data stream already exists
                if (
                    isinstance(stream, SportsDataStream)
                    and stream.sports_data_filter == subscription
                    and stream.streaming_timeout == strategy.streaming_timeout
                ):
                    logger.info(
                        "Using {0} ({1}) for strategy {2}".format(
                            strategy.stream_class, stream.stream_id, strategy
                        )
                    )
                    strategy.streams.append(stream)
                    break
            else:  # nope? lets create a new one
                stream_id = self._increment_stream_id()
                logger.info(
                    "Creating new {0} ({1}) for strategy {2}".format(
                        strategy.stream_class, stream_id, strategy
                    )
                )
                stream = SportsDataStream(
                    flumine=self.flumine,
                    stream_id=stream_id,
                    sports_data_filter=subscription,
                    streaming_timeout=strategy.streaming_timeout,
                )
                self._streams.append(stream)
                strategy.streams.append(stream)

    def add_historical_stream(
        self,
        strategy: BaseStrategy,
        market: str,
        event_processing: bool,
        **listener_kwargs
    ) -> HistoricalStream:
        for stream in self:
            if (
                stream.market_filter == market
                and stream.event_processing == event_processing
                and stream.listener_kwargs == listener_kwargs
            ):
                return stream
        else:
            stream_id = self._increment_stream_id()
            event_id = get_file_md(market, "eventId")
            if event_processing and event_id is None:
                logger.warning("EventId not found for market %s" % market)
            logger.info(
                "Creating new {0} ({1}) for strategy {2}".format(
                    HistoricalStream.__name__, stream_id, strategy
                ),
                extra={
                    "strategy": strategy,
                    "stream_id": stream_id,
                    "market_filter": market,
                    "event_id": event_id,
                    "event_processing": event_processing,
                },
            )
            stream = HistoricalStream(
                flumine=self.flumine,
                stream_id=stream_id,
                market_filter=market,
                market_data_filter=strategy.market_data_filter,
                streaming_timeout=strategy.streaming_timeout,
                conflate_ms=strategy.conflate_ms,
                output_queue=False,
                event_processing=event_processing,
                event_id=event_id,
                **listener_kwargs,
            )
            self._streams.append(stream)
            return stream

    """ order data """

    def add_order_stream(
        self,
        client: BaseClient,
        conflate_ms: int = None,
        streaming_timeout: float = 0.25,
    ) -> OrderStream:
        stream_id = self._increment_stream_id()
        stream = OrderStream(
            flumine=self.flumine,
            stream_id=stream_id,
            conflate_ms=conflate_ms,
            streaming_timeout=streaming_timeout,
            client=client,
        )
        self._streams.append(stream)
        return stream

    def add_simulated_order_stream(
        self,
        client: BaseClient,
        conflate_ms: int = None,
        streaming_timeout: float = 0.25,
    ) -> SimulatedOrderStream:
        logger.warning(
            "Client {0} now paper trading".format(client.betting_client.username)
        )
        stream_id = self._increment_stream_id()
        stream = SimulatedOrderStream(
            flumine=self.flumine,
            stream_id=stream_id,
            conflate_ms=conflate_ms,
            streaming_timeout=streaming_timeout,
            client=client,
            custom=True,
        )
        self._streams.append(stream)
        return stream

    """ custom stream """

    def add_custom_stream(self, stream):
        stream.stream_id = self._increment_stream_id()
        self._streams.append(stream)
        return stream

    def start(self) -> None:
        if not self.flumine.SIMULATED:
            logger.info("Starting streams..")
            for stream in self:
                stream.start()
                # wait for successful start
                while not stream.custom and not stream.stream_running:
                    time.sleep(0.25)

    def stop(self) -> None:
        for stream in self:
            stream.stop()

    def _increment_stream_id(self) -> int:
        self._stream_id += int(1e3)
        return self._stream_id

    def __iter__(self) -> Iterator[Union[MarketStream, DataStream, HistoricalStream]]:
        return iter(self._streams)

    def __len__(self) -> int:
        return len(self._streams)
