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
        """ Only uses _thread_pool if paper_trade
        """
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

        # todo if order_package.client.paper_trade:
        #     self._thread_pool.submit(func, order_package, None)
        # else:
        func(order_package, http_session=None)

    def execute_place(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        # todo if order_package.client.paper_trade:
        #     time.sleep(order_package.bet_delay + self.PLACE_LATENCY)

        for order in order_package:
            self._bet_id += 1
            simulated_response = order.simulated.place(order_package.market)
            self._order_logger(order, simulated_response, order_package.package_type)

            # if simulated_response.status

    def execute_cancel(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        raise NotImplementedError

    def execute_update(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        raise NotImplementedError

    def execute_replace(
        self, order_package, http_session: Optional[requests.Session]
    ) -> None:
        raise NotImplementedError
