import os
import unittest

from flumine import FlumineBacktest, clients, BaseStrategy, config
from flumine.order.trade import Trade
from flumine.order.order import OrderStatus
from flumine.order.ordertype import LimitOrder, MarketOnCloseOrder
from flumine.utils import get_price

SKIP_INTEGRATION_TESTS = int(os.environ.get("SKIP_INTEGRATION_TESTS", 1))


class IntegrationTest(unittest.TestCase):
    def test_backtest_basic(self):
        class Ex(BaseStrategy):
            def check_market_book(self, market, market_book):
                return True

            def process_market_book(self, market, market_book):
                return

        client = clients.BacktestClient()
        framework = FlumineBacktest(client=client)
        strategy = Ex(market_filter={"markets": ["tests/resources/BASIC-1.132153978"]})
        framework.add_strategy(strategy)
        framework.run()

    @unittest.skipIf(
        SKIP_INTEGRATION_TESTS,
        "Integrations tests (set env.SKIP_INTEGRATION_TESTS = 0)",
    )
    def test_backtest_pro(self):
        class LimitOrders(BaseStrategy):
            def check_market_book(self, market, market_book):
                if market_book.inplay:
                    return True

            def process_market_book(self, market, market_book):
                for runner in market_book.runners:
                    if runner.last_price_traded < 2:
                        lay = get_price(runner.ex.available_to_lay, 0)
                        trade = Trade(
                            market_book.market_id,
                            runner.selection_id,
                            runner.handicap,
                            self,
                        )
                        order = trade.create_order(
                            side="LAY",
                            order_type=LimitOrder(lay, 2.00),
                        )
                        self.place_order(market, order)

            def process_orders(self, market, orders):
                for order in orders:
                    if order.status == OrderStatus.EXECUTABLE:
                        if order.elapsed_seconds and order.elapsed_seconds > 2:
                            self.cancel_order(market, order)

        class MarketOnCloseOrders(BaseStrategy):
            def check_market_book(self, market, market_book):
                if not market_book.inplay and market.seconds_to_start < 100:
                    return True

            def process_market_book(self, market, market_book):
                for runner in market_book.runners:
                    runner_context = self.get_runner_context(
                        market.market_id, runner.selection_id
                    )
                    if runner_context.trade_count == 0:
                        trade = Trade(
                            market_book.market_id,
                            runner.selection_id,
                            runner.handicap,
                            self,
                        )
                        order = trade.create_order(
                            side="LAY",
                            order_type=MarketOnCloseOrder(100.00),
                        )
                        self.place_order(market, order)

        client = clients.BacktestClient()
        framework = FlumineBacktest(client=client)
        limit_strategy = LimitOrders(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
        )
        framework.add_strategy(limit_strategy)
        market_strategy = MarketOnCloseOrders(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
        )
        framework.add_strategy(market_strategy)
        framework.run()

        for market in framework.markets:
            limit_orders = [
                o for o in market.blotter if o.trade.strategy == limit_strategy
            ]
            self.assertEqual(
                round(sum([o.simulated.profit for o in limit_orders]), 2), 18.96
            )
            self.assertEqual(len(limit_orders), 15)

            market_orders = [
                o for o in market.blotter if o.trade.strategy == market_strategy
            ]
            self.assertEqual(
                round(sum([o.simulated.profit for o in market_orders]), 2), -6.68
            )
            self.assertEqual(len(market_orders), 14)

    def tearDown(self) -> None:
        config.simulated = False
