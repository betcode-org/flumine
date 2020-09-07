import time
import requests
from typing import Optional

from .baseexecution import BaseExecution
from ..clients.clients import ExchangeType
from ..order.orderpackage import BaseOrderPackage, OrderPackageType


class SimulatedExecution(BaseExecution):

    EXCHANGE = ExchangeType.SIMULATED
    PLACE_LATENCY = 0.120
    CANCEL_LATENCY = 0.170
    UPDATE_LATENCY = 0.150  # todo confirm?
    REPLACE_LATENCY = 0.280

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
            time.sleep(order_package.bet_delay + self.PLACE_LATENCY)
        market_book = order_package.market.market_book
        for order, instruction in zip(order_package, order_package.place_instructions):
            with order.trade:
                self._bet_id += 1
                simulated_response = order.simulated.place(
                    order_package.client, market_book, instruction, self._bet_id
                )
                self._order_logger(
                    order, simulated_response, order_package.package_type
                )
                if simulated_response.status == "SUCCESS":
                    order.executable()
                elif simulated_response.status == "FAILURE":
                    order.lapsed()

    def execute_cancel(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        if order_package.client.paper_trade:
            time.sleep(self.CANCEL_LATENCY)
        for order in order_package:
            with order.trade:
                simulated_response = order.simulated.cancel()
                self._order_logger(
                    order, simulated_response, order_package.package_type
                )
                if simulated_response.status == "SUCCESS":
                    order.execution_complete()
                elif simulated_response.status == "FAILURE":
                    order.executable()

    def execute_update(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        if order_package.client.paper_trade:
            time.sleep(self.UPDATE_LATENCY)
        for order, instruction in zip(order_package, order_package.update_instructions):
            with order.trade:
                simulated_response = order.simulated.update(instruction)
                self._order_logger(
                    order, simulated_response, order_package.package_type
                )
                if simulated_response.status == "SUCCESS":
                    order.executable()
                elif simulated_response.status == "FAILURE":
                    order.executable()

    def execute_replace(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        if (
            order_package.client.paper_trade
        ):  # todo should the cancel happen without a delay?
            time.sleep(order_package.bet_delay + self.REPLACE_LATENCY)
        market_book = order_package.market.market_book
        for order, instruction in zip(
            order_package, order_package.replace_instructions
        ):
            with order.trade:
                # cancel current order
                cancel_instruction_report = order.simulated.cancel()
                if cancel_instruction_report.status == "SUCCESS":
                    order.execution_complete()
                elif cancel_instruction_report.status == "FAILURE":
                    order.executable()  # todo do not carry out replace
                else:
                    order.lapsed()  # todo do not carry out replace
                self._order_logger(
                    order,
                    cancel_instruction_report,
                    OrderPackageType.CANCEL,
                )

                # place new order
                self._bet_id += 1
                replacement_order = order.trade.create_order_replacement(
                    order, instruction.get("newPrice")
                )
                place_instruction_report = replacement_order.simulated.place(
                    order_package.client, market_book, instruction, self._bet_id
                )
                if place_instruction_report.status == "SUCCESS":
                    self._order_logger(
                        replacement_order,
                        place_instruction_report,
                        order_package.package_type,
                    )
                    # add to blotter
                    market = order_package.market
                    market.place_order(replacement_order, execute=False)
                    replacement_order.executable()
                elif place_instruction_report.status == "FAILURE":
                    order.executable()
