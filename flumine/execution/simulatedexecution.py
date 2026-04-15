import time
import requests
from typing import Optional

from .. import config
from .baseexecution import BaseExecution
from ..clients.clients import VenueType
from ..order.order import OrderStatus
from ..order.orderpackage import BaseOrderPackage, OrderPackageType


class SimulatedExecution(BaseExecution):
    VENUE = VenueType.SIMULATED

    def handler(self, order_package: BaseOrderPackage) -> None:
        """Only uses _thread_pool if paper_trade"""
        if order_package.package_type == OrderPackageType.PLACE:
            func = self.execute_place
        elif order_package.package_type == OrderPackageType.CANCEL:
            func = self.execute_cancel
        elif order_package.package_type == OrderPackageType.UPDATE:
            func = self.execute_update
        elif order_package.package_type == OrderPackageType.REPLACE:
            func = self.execute_replace
        else:
            raise NotImplementedError()

        if order_package.client.paper_trade:
            self._thread_pool.submit(func, order_package, None)
        else:
            func(order_package, http_session=None)

    def execute_place(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        if order_package.client.paper_trade:
            # todo PASSIVE matching
            time.sleep(order_package.simulated_latency_plus_delay)
        market = self.flumine.markets.markets[order_package.market_id]
        market_book = market.market_book

        # calc current elapsed seconds
        elapsed_seconds = order_package.elapsed_seconds
        if elapsed_seconds < order_package.simulated_latency_plus_delay:
            # check if PASSIVE execution available
            if (
                market_book.market_definition.bet_delay_models is None
                or "PASSIVE" not in market_book.market_definition.bet_delay_models
            ):
                return

        for order, instruction in zip(
            order_package.orders_pending, order_package.place_instructions
        ):
            with order.trade:
                self._bet_id += 1
                simulated_response = order.simulated.place(
                    order_package, market_book, instruction, self._bet_id
                )
                if simulated_response.status == "DELAY":  # PENDING delay
                    self._bet_id -= 1
                    continue
                self._order_logger(
                    order, simulated_response, order_package.package_type
                )
                if simulated_response.status == "SUCCESS":
                    order.executable()
                elif simulated_response.status == "FAILURE":
                    order.execution_complete()
                # update transaction counts
                order_package.client.add_transaction(1)

    def execute_cancel(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        if order_package.client.paper_trade:
            time.sleep(order_package.simulated_latency_plus_delay)
        market = self.flumine.markets.markets[order_package.market_id]
        failed_transaction_count = 0
        for order in order_package:
            with order.trade:
                simulated_response = order.simulated.cancel(market.market_book)
                self._order_logger(
                    order, simulated_response, order_package.package_type
                )
                if simulated_response.status == "SUCCESS":
                    if order.size_remaining == 0:
                        order.execution_complete()
                    else:
                        order.executable()
                elif simulated_response.status == "FAILURE":
                    order.executable()
                    failed_transaction_count += 1

        # update transaction counts
        if failed_transaction_count:
            order_package.client.add_transaction(failed_transaction_count, failed=True)

    def execute_update(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        if order_package.client.paper_trade:
            time.sleep(order_package.simulated_latency_plus_delay)
        market = self.flumine.markets.markets[order_package.market_id]
        failed_transaction_count = 0
        for order, instruction in zip(order_package, order_package.update_instructions):
            with order.trade:
                simulated_response = order.simulated.update(
                    market.market_book, instruction
                )
                self._order_logger(
                    order, simulated_response, order_package.package_type
                )
                if simulated_response.status == "SUCCESS":
                    order.executable()
                elif simulated_response.status == "FAILURE":
                    order.executable()
                    failed_transaction_count += 1

        # update transaction counts
        if failed_transaction_count:
            order_package.client.add_transaction(failed_transaction_count, failed=True)

    def execute_replace(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        if order_package.client.paper_trade:
            # todo the cancel happens without a bet delay!
            # todo PASSIVE matching
            time.sleep(order_package.simulated_latency_plus_delay)
        market = self.flumine.markets.markets[order_package.market_id]
        market_book = market.market_book

        # calc current elapsed seconds
        elapsed_seconds = order_package.elapsed_seconds
        if elapsed_seconds < config.cancel_latency:
            return

        failed_transaction_count = 0
        for order in order_package.orders_pending:
            with order.trade:
                if order.status == OrderStatus.REPLACING:
                    # we can cancel after the latency (no bet delay)
                    instruction = order.create_replace_instruction()
                    # cancel current order
                    err = False
                    cancel_instruction_report = order.simulated.cancel(market_book)
                    if cancel_instruction_report.status == "SUCCESS":
                        order.execution_complete()
                    elif cancel_instruction_report.status == "FAILURE":
                        order.executable()
                        failed_transaction_count += 1
                        err = True
                    self._order_logger(
                        order,
                        cancel_instruction_report,
                        OrderPackageType.CANCEL,
                    )
                    if err:
                        continue

                    # create the replacement order
                    replacement_order = order.trade.create_order_replacement(
                        order,
                        instruction.get("newPrice"),
                        cancel_instruction_report.size_cancelled,
                        order_package.date_time_created,
                    )
                    replacement_order.placing()
                    order_package._orders.append(replacement_order)

                elif order.status == OrderStatus.PENDING:
                    # we can re'place' after the bet delay latency or PASSIVE
                    if elapsed_seconds < config.place_latency + order_package.bet_delay:
                        # check if PASSIVE execution available
                        if (
                            market_book.market_definition.bet_delay_models is None
                            or "PASSIVE"
                            not in market_book.market_definition.bet_delay_models
                        ):
                            return
                    instruction = order.create_place_instruction()
                    self._bet_id += 1
                    place_instruction_report = order.simulated.place(
                        order_package, market_book, instruction, self._bet_id
                    )
                    if place_instruction_report.status == "DELAY":  # PENDING delay
                        self._bet_id -= 1
                        continue
                    if place_instruction_report.status == "SUCCESS":
                        self._order_logger(
                            order,
                            place_instruction_report,
                            order_package.package_type,
                        )
                        # add to blotter
                        market.place_order(order, execute=False, client=order.client)
                        order.executable()
                    elif place_instruction_report.status == "FAILURE":
                        order.execution_complete()
                    # update transaction counts
                    order_package.client.add_transaction(1)

        if failed_transaction_count:
            order_package.client.add_transaction(failed_transaction_count, failed=True)
