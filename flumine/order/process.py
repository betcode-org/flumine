import logging

from ..markets.markets import Markets
from ..order.order import BaseOrder, OrderStatus

logger = logging.getLogger(__name__)

# todo handle fillkill/green/stop/


def process_current_orders(markets: Markets, event):
    for current_orders in event.event:
        for current_order in current_orders.orders:
            order = markets.get_order(
                market_id=current_order.market_id,
                customer_order_ref=current_order.customer_order_ref,
            )
            if order:
                # order.update_current_status(current_order)
                process_current_order(order)
            else:
                logger.warning(
                    "Order %s not present in blotter" % current_order.bet_id,
                    extra={
                        "bet_id": current_order.bet_id,
                        "market_id": current_order.market_id,
                        "customer_strategy_ref": current_order.customer_strategy_ref,
                        "customer_order_ref": current_order.customer_order_ref,
                    },
                )


def process_current_order(order: BaseOrder):
    if order.status == OrderStatus.EXECUTABLE:
        pass
        # print(order.status, order.status_log)
