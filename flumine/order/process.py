import logging

from .. import config
from ..markets.markets import Markets
from ..order.order import BaseOrder, OrderStatus, OrderTypes
from ..order.trade import Trade
from ..strategy.strategy import Strategies
from ..events.events import OrderEvent
from ..utils import STRATEGY_NAME_HASH_LENGTH

logger = logging.getLogger(__name__)

"""
Various functions to update current order status
and update status.

Loop through each current order:
    order = Lookup order in market using marketId and orderId
    if order is None (not present locally):
        create local order using data and make executable #todo!!!
    if betId is None (async placement):
        Update betId and log through logging_control
    if order betId != current_order betId:
        Get order using current_order betId due to replace request (new betId)
    if order:
        update current status
        process
"""


def process_current_orders(
    markets: Markets, strategies: Strategies, event, log_control
) -> None:
    for current_orders in event.event:
        for current_order in current_orders.orders:
            order_id = current_order.customer_order_ref[STRATEGY_NAME_HASH_LENGTH + 1 :]
            order = markets.get_order(
                market_id=current_order.market_id,
                order_id=order_id,
            )
            if order is None:
                logger.warning(
                    "Order %s not present in blotter" % current_order.bet_id,
                    extra={
                        "bet_id": current_order.bet_id,
                        "market_id": current_order.market_id,
                        "customer_strategy_ref": current_order.customer_strategy_ref,
                        "customer_order_ref": current_order.customer_order_ref,
                    },
                )
                order = create_order_from_current(markets, strategies, current_order)
                if order:
                    logger.info(
                        "Order %s added to blotter" % current_order.bet_id,
                        extra=order.info,
                    )
                    order.executable()  # todo correct?
                else:
                    continue

            if (
                config.async_place_orders
                and order.status == OrderStatus.PENDING
                and order.bet_id is None
                and current_order.bet_id
            ):  # async bet pending processing
                order.bet_id = current_order.bet_id
                log_control(OrderEvent(order))
                order.executable()
            elif order.bet_id != current_order.bet_id:  # replaceOrder handling (hacky)
                order = markets.get_order_from_bet_id(
                    market_id=current_order.market_id,
                    bet_id=current_order.bet_id,
                )

            if order:
                order.update_current_order(current_order)
                process_current_order(order)


def process_current_order(order: BaseOrder):
    if order.status == OrderStatus.EXECUTABLE:
        if order.order_type.ORDER_TYPE == OrderTypes.LIMIT:
            # todo use `order.current_order.status` ?
            if order.size_voided:
                order.voided()
            elif order.size_lapsed:
                order.lapsed()
            elif order.size_remaining == 0:
                order.execution_complete()
        elif order.order_type.ORDER_TYPE == OrderTypes.LIMIT_ON_CLOSE:
            if order.current_order.status == "EXECUTION_COMPLETE":
                order.execution_complete()
        elif order.order_type.ORDER_TYPE == OrderTypes.MARKET_ON_CLOSE:
            if order.current_order.status == "EXECUTION_COMPLETE":
                order.execution_complete()


def create_order_from_current(markets: Markets, strategies: Strategies, current_order):
    strategy_name_hash = current_order.customer_order_ref[:STRATEGY_NAME_HASH_LENGTH]
    order_id = current_order.customer_order_ref[STRATEGY_NAME_HASH_LENGTH + 1 :]
    # get market
    market = markets.markets.get(current_order.market_id)
    if market is None:
        logger.warning(
            "Market not available to create order {0}".format(order_id),
            extra={
                "bet_id": current_order.bet_id,
                "market_id": current_order.market_id,
                "customer_strategy_ref": current_order.customer_strategy_ref,
                "customer_order_ref": current_order.customer_order_ref,
                "strategy_name_hash": strategy_name_hash,
            },
        )
        return
    # get strategy
    strategy = strategies.hashes.get(strategy_name_hash)
    if strategy is None:
        logger.warning(
            "Strategy not available to create order {0}".format(order_id),
            extra={
                "bet_id": current_order.bet_id,
                "market_id": current_order.market_id,
                "customer_strategy_ref": current_order.customer_strategy_ref,
                "customer_order_ref": current_order.customer_order_ref,
                "strategy_name_hash": strategy_name_hash,
            },
        )
        return
    # add trade/order
    trade = Trade(
        market.market_id, current_order.selection_id, current_order.handicap, strategy
    )
    order = trade.create_order_from_current(current_order, order_id)
    market.blotter[order.id] = order
    runner_context = strategy.get_runner_context(*order.lookup)
    runner_context.place(trade.id)
    return order
