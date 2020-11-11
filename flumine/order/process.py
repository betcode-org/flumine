import logging

from ..markets.markets import Markets
from ..order.order import BaseOrder, OrderStatus, OrderTypes
from ..order.trade import Trade
from ..strategy.strategy import Strategies, STRATEGY_NAME_HASH_LENGTH

logger = logging.getLogger(__name__)

"""
Handles trade fillkill / green etc.
Handles orphan orders by creating empty trade and order data from CurrentOrder object/
"""


# todo handle fillkill/green/


def process_current_orders(markets: Markets, strategies: Strategies, event):
    for current_orders in event.event:
        for current_order in current_orders.orders:
            order_id = current_order.customer_order_ref[STRATEGY_NAME_HASH_LENGTH + 1 :]
            order = markets.get_order(
                market_id=current_order.market_id,
                order_id=order_id,
            )
            if not order:
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
            if order.bet_id != current_order.bet_id:  # replaceOrder handling (hacky)
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
    strategy_name_hash, order_id = current_order.customer_order_ref.split("-")
    # get market
    market = markets.markets.get(current_order.market_id)
    if market is None:
        # todo log
        return
    # get strategy
    strategy = strategies.hashes.get(strategy_name_hash)
    if strategy is None:
        # todo log
        return
    # add trade/order
    trade = Trade(
        market.market_id, current_order.selection_id, current_order.handicap, strategy
    )
    order = trade.create_order_from_current(current_order, order_id)
    market.blotter[order.id] = order
    return order
