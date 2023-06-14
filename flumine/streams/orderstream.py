import time
import queue
import logging
from betfairlightweight import BetfairError, filters
from tenacity import retry

from .basestream import BaseStream
from ..events.events import CurrentOrdersEvent
from .. import config

logger = logging.getLogger(__name__)

RETRY_WAIT = BaseStream.RETRY_WAIT
START_DELAY = 2
SNAP_DELTA = 5


class OrderStream(BaseStream):
    @retry(wait=RETRY_WAIT)
    def run(self) -> None:
        logger.info(
            "Starting OrderStream {0}".format(self.stream_id),
            extra={
                "stream_id": self.stream_id,
                "customer_strategy_refs": config.customer_strategy_ref,
                "conflate_ms": self.conflate_ms,
                "streaming_timeout": self.streaming_timeout,
                "client_username": self.client.username,
            },
        )
        if not self._output_thread.is_alive():
            logger.info(
                "Starting output_thread (OrderStream {0})".format(self.stream_id)
            )
            self._output_thread.start()

        self._stream = self.betting_client.streaming.create_stream(
            unique_id=self.stream_id, listener=self._listener
        )
        try:
            self.stream_id = self._stream.subscribe_to_orders(
                order_filter=filters.streaming_order_filter(
                    customer_strategy_refs=[config.customer_strategy_ref]
                    if config.customer_strategy_ref
                    else None,
                    partition_matched_by_strategy_ref=True,
                    include_overall_position=False,
                ),
                conflate_ms=self.conflate_ms,
            )
            self._stream.start()
        except BetfairError:
            logger.error(
                "OrderStream {0} run error".format(self.stream_id), exc_info=True
            )
            raise
        except Exception:
            logger.critical(
                "OrderStream {0} run error".format(self.stream_id), exc_info=True
            )
            raise
        logger.info("Stopped OrderStream {0}".format(self.stream_id))

    def handle_output(self) -> None:
        """Handles output from stream, snaps
        if live orders or time delta greater
        than SNAP_DELTA.
        """
        last_snap = 1
        while self.is_alive():
            try:
                order_books = self._output_queue.get(
                    block=True, timeout=self.streaming_timeout
                )
            except queue.Empty:
                active_open_markets = [
                    m
                    for m in self.flumine.markets
                    if m.blotter.active and m.status == "OPEN"
                ]
                if active_open_markets or (time.time() - last_snap) > SNAP_DELTA:
                    order_books = []
                else:
                    continue
            last_snap = time.time()
            if order_books or self.flumine.markets.live_orders:
                for order_book in order_books:
                    order_book.client = self.client
                self.flumine.handler_queue.put(CurrentOrdersEvent(order_books))

        logger.info("Stopped output_thread (OrderStream {0})".format(self.stream_id))
