import unittest
from unittest import mock

from flumine import worker


class BackgroundWorkerTest(unittest.TestCase):
    def setUp(self):
        self.mock_function = mock.Mock()
        self.worker = worker.BackgroundWorker(
            123, self.mock_function, (1, 2), {"hello": "world"}, 5
        )

    def test_init(self):
        self.assertEqual(self.worker.interval, 123)
        self.assertEqual(self.worker.function, self.mock_function)
        self.assertEqual(self.worker.func_args, (1, 2))
        self.assertEqual(self.worker.func_kwargs, {"hello": "world"})
        self.assertEqual(self.worker.start_delay, 5)

    # def test_run(self):
    #     self.worker.run()


class WorkersTest(unittest.TestCase):
    def test_keep_alive(self):
        mock_client = mock.Mock()
        mock_client.betting_client.session_token = None
        worker.keep_alive(mock_client)
        mock_client.login.assert_called_with()

        mock_client.betting_client.session_token = 1
        mock_client.betting_client.session_expired = True
        worker.keep_alive(mock_client)
        mock_client.keep_alive.assert_called_with()

    @mock.patch("flumine.worker.MarketCatalogueEvent")
    def test_poll_market_catalogue(self, mock_event):
        mock_client = mock.Mock()
        mock_markets = mock.Mock()
        mock_markets.markets = {"1.234": None, "5.678": None}
        mock_handler_queue = mock.Mock()

        worker.poll_market_catalogue(mock_client, mock_markets, mock_handler_queue)
        mock_client.betting_client.betting.list_market_catalogue.assert_called_with(
            filter={"marketIds": list(mock_markets.markets.keys())},
            market_projection=[
                "COMPETITION",
                "EVENT",
                "EVENT_TYPE",
                "RUNNER_DESCRIPTION",
                "RUNNER_METADATA",
                "MARKET_START_TIME",
                "MARKET_DESCRIPTION",
            ],
            max_results=100,
        )
        mock_handler_queue.put.assert_called_with(mock_event())
