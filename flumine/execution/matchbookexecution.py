import logging
import requests
from typing import Callable

from ..clients import VenueType
from .baseexecution import BaseExecution
from ..exceptions import OrderExecutionError
from ..order.order import BaseOrder
from ..order.orderpackage import BaseOrderPackage, OrderPackageType
from ..events.events import OrderEvent

logger = logging.getLogger(__name__)


class MatchbookExecution(BaseExecution):
    """
    Matchbook execution for place, cancel and update
    """

    VENUE = VenueType.MATCHBOOK

    def execute_place(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.place, order_package)
        if response:
            order_lookup = {int(o.id): o for o in order_package}
            for offer in response.offers:
                # get order (can't rely on the order they are returned)
                order = order_lookup.pop(int(offer.temp_id))
                with order.trade:
                    self._order_logger(order, offer, order_package.package_type)
                    status = offer.status
                    if status == "failed":
                        logger.error(
                            "execute_place: Order error return code",
                            extra={
                                "order_id": int(order.id),
                                "status": status,
                                "response": offer,
                            },
                        )
                        order.execution_complete()
                    elif status == "delayed":
                        pass  # Offer submission was delayed due to in-play market
                    else:
                        order.executable()  # let process.py pick it up
            # todo update transaction counts
        else:
            # reset on error so that they can be picked back up
            for order in order_package:
                with order.trade:
                    order.execution_complete()

    def place(self, order_package: BaseOrderPackage):
        return order_package.client.betting_client.submit_offers(
            offers=order_package.place_instructions
        )

    def execute_cancel(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.cancel, order_package)
        if response:
            order_lookup = {int(o.id): o for o in order_package}
            for offer in response.offers:
                # get order (can't rely on the order they are returned)
                order = order_lookup.pop(int(offer.temp_id))
                with order.trade:
                    self._order_logger(order, offer, order_package.package_type)
                    order.execution_complete()
            # reset any not returned so that they can be picked back up
            for order in order_lookup.values():
                with order.trade:
                    order.executable()
        else:
            # reset on error so that they can be picked back up
            for order in order_package:
                with order.trade:
                    order.executable()

    def cancel(self, order_package: BaseOrderPackage):
        return order_package.client.betting_client.cancel_offers(
            offer_ids=order_package.cancel_instructions
        )

    def execute_update(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.update, order_package)
        if response:
            order_lookup = {int(o.id): o for o in order_package}
            for offer in response.offers:
                # get order (can't rely on the order they are returned)
                order = order_lookup.pop(int(offer.temp_id))
                with order.trade:
                    self._order_logger(order, offer, order_package.package_type)
                    status = offer.status

                    if status == "failed":
                        logger.error(
                            "execute_update: Order error return code",
                            extra={
                                "order_id": int(order.id),
                                "status": status,
                                "response": offer,
                            },
                        )
                        order.executable()
                    else:
                        pass  # let process.py pick it up
        else:
            # reset on error so that they can be picked back up
            for order in order_package:
                with order.trade:
                    order.executable()

    def update(self, order_package: BaseOrderPackage):
        # temp copy to prevent an empty list of instructions sent
        # this can occur if order is matched during the execution
        order_list = list(order_package.update_instructions)
        if not order_list:
            logger.warning("Empty `order_list`", extra=order_package.info)
            raise OrderExecutionError()
        return order_package.client.betting_client.edit_offers(edits=order_list)

    def _execution_helper(
        self,
        trading_function: Callable,
        order_package: BaseOrderPackage,
    ):
        try:
            response = trading_function(order_package)
        except Exception as e:
            logger.error(
                "Execution error",
                extra={
                    "trading_function": trading_function.__name__,
                    "response": e,
                    "order_package": order_package.info,
                },
                exc_info=True,
            )
            return
        except Exception as e:
            logger.critical(
                "Execution unknown error",
                extra={
                    "trading_function": trading_function.__name__,
                    "response": e,
                    "order_package": order_package.info,
                },
                exc_info=True,
            )
            return
        logger.info(
            f"execute_{trading_function.__name__}",
            extra={
                "trading_function": trading_function.__name__,
                "response": response,
                "order_package": order_package.info,
            },
        )
        return response

    def _order_logger(self, order: BaseOrder, offer, package_type: OrderPackageType):
        logger.info(
            "Order %s: %s",
            package_type.value,
            offer.status,
            extra={
                "bet_id": order.bet_id,
                "order_id": order.id,
                "status": offer.status,
            },
        )
        if package_type == OrderPackageType.PLACE:
            dt = True if offer.id else False
            order.responses.placed(offer, dt=dt)
            if offer.id:
                order.bet_id = offer.id
                self.flumine.log_control(OrderEvent(order, venue=order.VENUE))
        elif package_type == OrderPackageType.CANCEL:
            order.responses.cancelled(offer)
        elif package_type == OrderPackageType.UPDATE:
            order.responses.updated(offer)
