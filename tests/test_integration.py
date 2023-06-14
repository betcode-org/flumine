import unittest

from flumine import FlumineSimulation, clients, BaseStrategy, config
from flumine.order.trade import Trade
from flumine.order.order import OrderStatus
from flumine.order.ordertype import LimitOrder, MarketOnCloseOrder, LimitOnCloseOrder
from flumine.utils import get_price, get_nearest_price


class IntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        # change config to raise errors
        config.raise_errors = True

    def test_simulation_basic(self):
        class Ex(BaseStrategy):
            def check_market_book(self, market, market_book):
                return True

            def process_market_book(self, market, market_book):
                return

        client = clients.SimulatedClient()
        framework = FlumineSimulation(client=client)
        strategy = Ex(market_filter={"markets": ["tests/resources/BASIC-1.132153978"]})
        framework.add_strategy(strategy)
        framework.run()

    def test_simulation_pro(self):
        class LimitOrders(BaseStrategy):
            def check_market_book(self, market, market_book):
                if not market_book.inplay and market.seconds_to_start < 100:
                    return True

            def process_market_book(self, market, market_book):
                with market.transaction() as t:
                    for runner in market_book.runners:
                        if runner.status == "ACTIVE":
                            back = get_price(runner.ex.available_to_back, 0)
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
                                    side="BACK",
                                    order_type=LimitOrder(back, 2.00),
                                )
                                t.place_order(order)

        class LimitReplaceOrders(BaseStrategy):
            def check_market_book(self, market, market_book):
                if not market_book.inplay and market.seconds_to_start < 100:
                    return True

            def process_market_book(self, market, market_book):
                with market.transaction() as t:
                    for runner in market_book.runners:
                        if runner.status == "ACTIVE":
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
                                    side="BACK",
                                    order_type=LimitOrder(1000, 2.00),
                                )
                                t.place_order(order)

            def process_orders(self, market, orders: list) -> None:
                with market.transaction() as t:
                    for order in orders:
                        if order.status == OrderStatus.EXECUTABLE:
                            if order.size_matched == 0:
                                t.replace_order(order, new_price=1.01)

        class LimitOrdersInplay(BaseStrategy):
            def check_market_book(self, market, market_book):
                if market_book.inplay:
                    return True

            def process_market_book(self, market, market_book):
                for runner in market_book.runners:
                    if runner.status == "ACTIVE" and runner.last_price_traded < 2:
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
                        market.place_order(order)

            def process_orders(self, market, orders):
                for order in orders:
                    if order.status == OrderStatus.EXECUTABLE:
                        if order.elapsed_seconds and order.elapsed_seconds > 2:
                            market.cancel_order(order)

        class LimitOnCloseOrders(BaseStrategy):
            def check_market_book(self, market, market_book):
                if not market_book.inplay and market.seconds_to_start < 100:
                    return True

            def process_market_book(self, market, market_book):
                for runner in market_book.runners:
                    if runner.status == "ACTIVE":
                        runner_context = self.get_runner_context(
                            market.market_id, runner.selection_id
                        )
                        if runner_context.trade_count == 0:
                            back = get_price(runner.ex.available_to_back, 0)
                            trade = Trade(
                                market_book.market_id,
                                runner.selection_id,
                                runner.handicap,
                                self,
                            )
                            order = trade.create_order(
                                side="BACK",
                                order_type=LimitOnCloseOrder(liability=10, price=back),
                            )
                            market.place_order(order)

        class MarketOnCloseOrders(BaseStrategy):
            def check_market_book(self, market, market_book):
                if not market_book.inplay and market.seconds_to_start < 100:
                    return True

            def process_market_book(self, market, market_book):
                for runner in market_book.runners:
                    if runner.status == "ACTIVE":
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
                            market.place_order(order)

        client = clients.SimulatedClient()
        framework = FlumineSimulation(client=client)
        limit_strategy = LimitOrders(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
            max_trade_count=1,
        )
        framework.add_strategy(limit_strategy)
        limit_replace_strategy = LimitReplaceOrders(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
            max_trade_count=1,
        )
        framework.add_strategy(limit_replace_strategy)
        limit_inplay_strategy = LimitOrdersInplay(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
        )
        framework.add_strategy(limit_inplay_strategy)
        limit_on_close_strategy = LimitOnCloseOrders(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
        )
        framework.add_strategy(limit_on_close_strategy)
        market_strategy = MarketOnCloseOrders(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
        )
        framework.add_strategy(market_strategy)
        framework.run()

        self.assertEqual(len(framework.markets), 1)

        for market in framework.markets:
            limit_orders = market.blotter.strategy_orders(limit_strategy)
            self.assertEqual(round(sum([o.profit for o in limit_orders]), 2), -16.8)
            self.assertEqual(len(limit_orders), 14)
            limit_replace_orders = market.blotter.strategy_orders(
                limit_replace_strategy
            )
            self.assertEqual(
                round(sum([o.profit for o in limit_replace_orders]), 2), -16.8
            )
            self.assertEqual(len(limit_replace_orders), 28)
            limit_inplay_orders = market.blotter.strategy_orders(limit_inplay_strategy)
            self.assertEqual(
                round(sum([o.profit for o in limit_inplay_orders]), 2), 19.88
            )
            self.assertEqual(len(limit_inplay_orders), 14)
            limit_on_close_orders = market.blotter.strategy_orders(
                limit_on_close_strategy
            )
            self.assertEqual(
                round(sum([o.profit for o in limit_on_close_orders]), 2), -53.20
            )
            self.assertEqual(len(limit_on_close_orders), 14)
            market_orders = market.blotter.strategy_orders(market_strategy)
            self.assertEqual(round(sum([o.profit for o in market_orders]), 2), -6.68)
            self.assertEqual(len(market_orders), 14)
            # check transaction count
            self.assertEqual(market._transaction_id, 5196)

    def test_simulation_multi_clients(self):
        class LimitOrders(BaseStrategy):
            def check_market_book(self, market, market_book):
                if market_book.inplay:
                    return True

            def process_market_book(self, market, market_book):
                with market.transaction(client=self.context["client"]) as t:
                    for runner in market_book.runners:
                        if runner.status == "ACTIVE":
                            back = get_price(runner.ex.available_to_back, 0)
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
                                    side="BACK",
                                    order_type=LimitOrder(back, 2.00),
                                )
                                t.place_order(order)

            def process_orders(self, market, orders):
                for order in orders:
                    if order.status == OrderStatus.EXECUTABLE:
                        if order.elapsed_seconds and order.elapsed_seconds > 2:
                            new_price = get_nearest_price(order.order_type.price - 1)
                            market.replace_order(order, new_price)
                        elif order.elapsed_seconds and order.elapsed_seconds > 10:
                            market.cancel_order(order)

        client_bpe_on = clients.SimulatedClient()
        client_bpe_off = clients.SimulatedClient(best_price_execution=False)
        framework = FlumineSimulation()
        framework.add_client(client_bpe_on)
        framework.add_client(client_bpe_off)
        limit_strategy_bpe_on = LimitOrders(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
            max_trade_count=100,
            context={"client": client_bpe_on},
        )
        framework.add_strategy(limit_strategy_bpe_on)
        limit_strategy_bpe_off = LimitOrders(
            market_filter={"markets": ["tests/resources/PRO-1.170258213"]},
            max_order_exposure=1000,
            max_selection_exposure=105,
            max_trade_count=100,
            context={"client": client_bpe_off},
        )
        framework.add_strategy(limit_strategy_bpe_off)
        framework.run()

        self.assertEqual(len(framework.markets), 1)

        for market in framework.markets:
            limit_orders_bpe_on = market.blotter.strategy_orders(limit_strategy_bpe_on)
            self.assertEqual(
                limit_orders_bpe_on, market.blotter.client_orders(client_bpe_on)
            )
            self.assertEqual(
                round(sum([o.profit for o in limit_orders_bpe_on]), 2), -17.75
            )
            self.assertEqual(len(limit_orders_bpe_on), 15)
            limit_orders_bpe_off = market.blotter.strategy_orders(
                limit_strategy_bpe_off
            )
            self.assertEqual(
                limit_orders_bpe_off, market.blotter.client_orders(client_bpe_off)
            )
            self.assertEqual(
                round(sum([o.profit for o in limit_orders_bpe_off]), 2),
                -19.75,
            )
            self.assertEqual(len(limit_orders_bpe_off), 14)

    def test_event_processing(self):
        client = clients.SimulatedClient()
        framework = FlumineSimulation(client=client)

        class LimitOrdersInplay(BaseStrategy):
            def check_market_book(self, market, market_book):
                if market_book.inplay:
                    return True

            def process_market_book(self, market, market_book):
                for runner in market_book.runners:
                    if runner.status == "ACTIVE" and runner.last_price_traded < 2:
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
                        market.place_order(order)

            def process_orders(self, market, orders):
                for order in orders:
                    if order.status == OrderStatus.EXECUTABLE:
                        if order.elapsed_seconds and order.elapsed_seconds > 2:
                            market.cancel_order(order)

        limit_inplay_strategy = LimitOrdersInplay(
            market_filter={
                "markets": [
                    "tests/resources/SELF-1.181223994",
                    "tests/resources/SELF-1.181223995",
                    "tests/resources/PRO-1.170258213",
                ],
                "event_processing": True,
            },
            max_order_exposure=1000,
            max_selection_exposure=105,
        )
        framework.add_strategy(limit_inplay_strategy)
        framework.run()

        self.assertEqual(len(framework.markets), 3)

        # Different event
        win_market = framework.markets.markets["1.170258213"]
        limit_inplay_orders = win_market.blotter.strategy_orders(limit_inplay_strategy)
        self.assertEqual(round(sum([o.profit for o in limit_inplay_orders]), 2), 19.88)
        self.assertEqual(len(limit_inplay_orders), 14)
        self.assertEqual(win_market._transaction_id, 165)

        # Same event
        win_market = framework.markets.markets["1.181223994"]
        limit_inplay_orders = win_market.blotter.strategy_orders(limit_inplay_strategy)
        self.assertEqual(round(sum([o.profit for o in limit_inplay_orders]), 2), 101.44)
        self.assertEqual(len(limit_inplay_orders), 86)
        self.assertEqual(win_market._transaction_id, 1329)

        place_market = framework.markets.markets["1.181223995"]
        limit_inplay_orders = place_market.blotter.strategy_orders(
            limit_inplay_strategy
        )
        self.assertEqual(round(sum([o.profit for o in limit_inplay_orders]), 2), -95.02)
        self.assertEqual(len(limit_inplay_orders), 200)
        self.assertEqual(place_market._transaction_id, 2436)

    def tearDown(self) -> None:
        config.simulated = False
        config.raise_errors = False
