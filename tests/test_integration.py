import unittest

from flumine import FlumineBacktest, clients, BaseStrategy, config


class IntegrationTest(unittest.TestCase):
    def test_backtest(self):
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

    def tearDown(self) -> None:
        config.simulated = False
