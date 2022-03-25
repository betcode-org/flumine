import logging
from flumine import config
from flumine.utils import STRATEGY_NAME_HASH_LENGTH
from flumine.markets.middleware import Middleware
from flumine.order.trade import Trade

logger = logging.getLogger(__name__)


class OrdersMiddleware(Middleware):
    """
    Middleware to add execution complete orders
    to the blotter. This is required on a restart
    as the order stream does not include
    EXECUTION_COMPLETE orders
    """

    def __init__(self, flumine):
        self.flumine = flumine

    def add_market(self, market) -> None:
        for client in self.flumine.clients:
            resp = client.betting_client.betting.list_current_orders(
                customer_strategy_refs=[config.customer_strategy_ref],
                order_projection="EXECUTION_COMPLETE",
            )
            for current_order in resp.orders:
                logger.info(
                    "OrdersMiddleware: Processing order {0}".format(
                        current_order.bet_id
                    ),
                    extra={
                        "bet_id": current_order.bet_id,
                        "market_id": current_order.market_id,
                        "customer_strategy_ref": current_order.customer_strategy_ref,
                        "customer_order_ref": current_order.customer_order_ref,
                        "client_username": client.username,
                    },
                )
                order = self._create_order_from_current(client, current_order, market)
                if order:
                    order.update_current_order(current_order)
                    order.execution_complete()

    def _create_order_from_current(self, client, current_order, market):
        strategy_name_hash = current_order.customer_order_ref[
            :STRATEGY_NAME_HASH_LENGTH
        ]
        order_id = current_order.customer_order_ref[STRATEGY_NAME_HASH_LENGTH + 1 :]
        # get strategy
        strategy = self.flumine.strategies.hashes.get(strategy_name_hash)
        if strategy is None:
            logger.warning(
                "OrdersMiddleware: Strategy not available to create order {0}".format(
                    order_id
                ),
                extra={
                    "bet_id": current_order.bet_id,
                    "market_id": current_order.market_id,
                    "customer_strategy_ref": current_order.customer_strategy_ref,
                    "customer_order_ref": current_order.customer_order_ref,
                    "strategy_name": str(strategy),
                    "client_username": client.username,
                },
            )
            return
        # add trade/order
        trade = Trade(
            market.market_id,
            current_order.selection_id,
            current_order.handicap,
            strategy,
        )
        order = trade.create_order_from_current(client, current_order, order_id)
        market.blotter[order.id] = order
        runner_context = strategy.get_runner_context(*order.lookup)
        runner_context.place(trade.id)
        logger.info(
            "OrdersMiddleware: New order trade created",
            extra={
                "bet_id": current_order.bet_id,
                "market_id": current_order.market_id,
                "customer_strategy_ref": current_order.customer_strategy_ref,
                "customer_order_ref": current_order.customer_order_ref,
                "strategy_name": str(strategy),
                "client_username": client.username,
            },
        )
        return order
