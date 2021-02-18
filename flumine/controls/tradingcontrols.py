import logging

from ..clients.clients import ExchangeType
from ..order.ordertype import OrderTypes
from ..order.orderpackage import OrderPackageType, BaseOrder
from . import BaseControl
from .. import utils

logger = logging.getLogger(__name__)


class OrderValidation(BaseControl):

    """
    Checks order price and size is valid for
    exchange.
    """

    NAME = "ORDER_VALIDATION"

    def _validate(self, order: BaseOrder, package_type: OrderPackageType) -> None:
        if order.EXCHANGE == ExchangeType.BETFAIR:
            self._validate_betfair_order(order)

    def _validate_betfair_order(self, order):
        if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            self._validate_betfair_size(order)
            self._validate_betfair_price(order)
            self._validate_betfair_min_size(order, OrderTypes.LIMIT)
        elif order.order_type.ORDER_TYPE == OrderTypes.LIMIT_ON_CLOSE:
            self._validate_betfair_price(order)
            self._validate_betfair_liability(order)
            self._validate_betfair_min_size(order, OrderTypes.LIMIT_ON_CLOSE)
        elif order.order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE:
            self._validate_betfair_liability(order)
            self._validate_betfair_min_size(order, OrderTypes.MARKET_ON_CLOSE)
        else:
            self._on_error(order, "Unknown orderType")

    def _validate_betfair_size(self, order):
        if order.order_type.size is None:
            self._on_error(order, "Order size is None")
        elif order.order_type.size <= 0:
            self._on_error(order, "Order size is less than 0")
        elif order.order_type.size != round(order.order_type.size, 2):
            self._on_error(order, "Order size has more than 2dp")

    def _validate_betfair_price(self, order):
        if order.order_type.price is None:
            self._on_error(order, "Order price is None")
        elif utils.as_dec(order.order_type.price) not in utils.PRICES:
            self._on_error(order, "Order price is not valid")

    def _validate_betfair_liability(self, order):
        if order.order_type.liability is None:
            self._on_error(order, "Order liability is None")
        elif order.order_type.liability <= 0:
            self._on_error(order, "Order liability is less than 0")

    def _validate_betfair_min_size(self, order, order_type):
        client = self.flumine.client
        if client.min_bet_validation is False:
            return  # some accounts do not have min bet restrictions
        if order_type == OrderTypes.LIMIT:
            if (
                order.order_type.size < client.min_bet_size
                and (order.order_type.price * order.order_type.size)
                < client.min_bet_payout
            ):
                self._on_error(
                    order,
                    "Order size is less than min bet size ({0}) or payout ({1}) for currency".format(
                        client.min_bet_size, client.min_bet_payout
                    ),
                )
        else:  # todo is this correct?
            if (
                order.side == "BACK"
                and order.order_type.liability < client.min_bet_size
            ):
                self._on_error(
                    order,
                    "Liability is less than min bet size ({0}) for currency".format(
                        client.min_bet_size
                    ),
                )
            elif (
                order.side == "LAY"
                and order.order_type.liability < client.min_bsp_liability
            ):
                self._on_error(
                    order,
                    "Liability is less than min BSP payout ({0}) for currency".format(
                        client.min_bsp_liability
                    ),
                )


class StrategyExposure(BaseControl):

    """
    Checks exposure does not exceed strategy
    max exposure.
    """

    NAME = "STRATEGY_EXPOSURE"

    def _validate(self, order: BaseOrder, package_type: OrderPackageType) -> None:
        if package_type == OrderPackageType.PLACE:
            # strategy.validate_order
            runner_context = order.trade.strategy.get_runner_context(*order.lookup)
            if order.trade.strategy.validate_order(runner_context, order) is False:
                return self._on_error(order, "strategy.validate_order failure")

        if package_type in (
            OrderPackageType.PLACE,
            OrderPackageType.REPLACE,  # todo potential bug?
        ):
            strategy = order.trade.strategy
            if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
                if order.side == "BACK":
                    exposure = order.order_type.size
                else:
                    exposure = (order.order_type.price - 1) * order.order_type.size
            elif order.order_type.ORDER_TYPE == OrderTypes.LIMIT_ON_CLOSE:
                exposure = order.order_type.liability  # todo correct?
            elif order.order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE:
                exposure = order.order_type.liability
            else:
                return self._on_error(order, "Unknown order_type")

            # per order
            if exposure > strategy.max_order_exposure:
                return self._on_error(
                    order,
                    "Order exposure ({0}) is greater than strategy.max_order_exposure ({1})".format(
                        exposure, strategy.max_order_exposure
                    ),
                )

            # per selection
            market = self.flumine.markets.markets[order.market_id]
            exposure = market.blotter.selection_exposure(strategy, lookup=order.lookup)
            if exposure > strategy.max_selection_exposure:
                return self._on_error(
                    order,
                    "Potential selection exposure ({0}) is greater than strategy.max_selection_exposure ({1})".format(
                        exposure,
                        strategy.max_selection_exposure,
                    ),
                )
