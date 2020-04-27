import logging

from ..clients.clients import ExchangeType
from ..order.ordertype import OrderTypes
from ..order.orderpackage import OrderPackageType
from . import BaseControl
from .. import utils

logger = logging.getLogger(__name__)


class OrderValidation(BaseControl):

    """
    Checks order price and size is valid for
    exchange.
    """

    NAME = "ORDER_VALIDATION"

    def _validate(self, order_package):
        for order in order_package:
            if order.EXCHANGE == ExchangeType.BETFAIR:
                self._validate_betfair_order(order)

    def _validate_betfair_order(self, order):
        if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            self._validate_betfair_size(order)
            self._validate_betfair_price(order)
        elif order.order_type.ORDER_TYPE == OrderTypes.LIMIT_ON_CLOSE:
            self._validate_betfair_price(order)
            self._validate_betfair_liability(order)
            self._validate_betfair_min_size(order)
        elif order.order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE:
            self._validate_betfair_liability(order)
            self._validate_betfair_min_size(order)
        else:
            self._on_error(order)  # unknown orderType

    def _validate_betfair_size(self, order):
        if order.order_type.size is None:
            self._on_error(order)
        elif order.order_type.size <= 0:
            self._on_error(order)
        elif order.order_type.size != round(order.order_type.size, 2):
            self._on_error(order)

    def _validate_betfair_price(self, order):
        if order.order_type.price is None:
            self._on_error(order)
        elif utils.as_dec(order.order_type.price) not in utils.PRICES:
            self._on_error(order)

    def _validate_betfair_liability(self, order):
        if order.order_type.liability is None:
            self._on_error(order)
        elif order.order_type.liability <= 0:
            self._on_error(order)

    def _validate_betfair_min_size(self, order):
        client = order.client
        if order.side == "BACK" and order.order_type.liability < client.min_bet_size:
            self._on_error(order)
        elif (
            order.side == "LAY"
            and order.order_type.liability < client.min_bsp_liability
        ):
            self._on_error(order)


class StrategyExposure(BaseControl):

    """
    Checks exposure does not breach strategy
    max exposure.
    """

    NAME = "STRATEGY_EXPOSURE"

    def _validate(self, order_package):
        if order_package.package_type in (
            OrderPackageType.PLACE,
            OrderPackageType.REPLACE,
        ):
            for order in order_package:
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
                    continue

                if exposure > strategy.max_order_exposure:
                    self._on_error(order)
                    continue

                current_selection_exposure = 0  # todo from blotter
                if (
                    current_selection_exposure + exposure
                ) > strategy.max_selection_exposure:
                    self._on_error(order)
