import unittest
from unittest import mock

from flumine.clients.clients import ExchangeType
from flumine.clients import BaseClient, BetfairClient, BacktestClient


class ClientsTest(unittest.TestCase):
    def test_exchange_type(self):
        assert ExchangeType


class BaseClientTest(unittest.TestCase):
    def setUp(self):
        self.mock_betting_client = mock.Mock()
        self.base_client = BaseClient(self.mock_betting_client, 1024, 100, 0.02, True)

    def test_init(self):
        self.assertEqual(self.base_client.betting_client, self.mock_betting_client)
        self.assertEqual(self.base_client.transaction_limit, 1024)
        self.assertEqual(self.base_client.capital_base, 100)
        self.assertEqual(self.base_client.commission_base, 0.02)
        self.assertTrue(self.base_client.interactive_login)
        self.assertIsNone(self.base_client.account_details)
        self.assertIsNone(self.base_client.account_funds)
        self.assertEqual(self.base_client.commission_paid, 0)
        self.assertEqual(self.base_client.chargeable_transaction_count, 0)
        self.assertIsNone(self.base_client.execution)
        self.assertEqual(self.base_client.trading_controls, [])

    def test_login(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.login()

    def test_keep_alive(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.keep_alive()

    def test_logout(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.logout()

    def test_update_account_details(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.update_account_details()

    def test_add_execution(self):
        mock_flumine = mock.Mock()
        self.base_client.EXCHANGE = ExchangeType.SIMULATED
        self.base_client.add_execution(mock_flumine)
        self.assertEqual(self.base_client.execution, mock_flumine.simulated_execution)
        self.base_client.EXCHANGE = ExchangeType.BETFAIR
        self.base_client.add_execution(mock_flumine)
        self.assertEqual(self.base_client.execution, mock_flumine.betfair_execution)

    def test_min_bet_size(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.min_bet_size

    def test_min_bet_payout(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.min_bet_payout

    def test_min_bsp_liability(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.min_bsp_liability


class BetfairClientTest(unittest.TestCase):
    def setUp(self):
        self.mock_betting_client = mock.Mock()
        self.betfair_client = BetfairClient(self.mock_betting_client)

    def test_login(self):
        self.betfair_client.login()
        self.mock_betting_client.login.assert_called_with()

    def test_login_no_certs(self):
        self.betfair_client.interactive_login = True
        self.betfair_client.login()
        self.mock_betting_client.login_interactive.assert_called_with()

    def test_keep_alive(self):
        self.mock_betting_client.session_expired = True
        self.betfair_client.keep_alive()
        self.mock_betting_client.keep_alive.assert_called_with()

    def test_logout(self):
        self.betfair_client.logout()
        self.mock_betting_client.logout.assert_called_with()

    @mock.patch("flumine.clients.betfairclient.BetfairClient._get_account_details")
    @mock.patch("flumine.clients.betfairclient.BetfairClient._get_account_funds")
    def test_update_account_details(self, mock_get_funds, mock_get_details):
        self.betfair_client.update_account_details()
        mock_get_funds.assert_called_with()
        mock_get_details.assert_called_with()
        self.assertEqual(self.betfair_client.account_details, mock_get_details())
        self.assertEqual(self.betfair_client.account_funds, mock_get_funds())

    def test__get_account_details(self):
        self.betfair_client._get_account_details()
        self.mock_betting_client.account.get_account_details.assert_called_with()

    def test__get_account_funds(self):
        self.betfair_client._get_account_funds()
        self.mock_betting_client.account.get_account_funds.assert_called_with()

    def test_min_bet_size(self):
        mock_account_details = mock.Mock()
        mock_account_details.currency_code = "GBP"
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_size, 2)

    def test_min_bet_size_none(self):
        mock_account_details = mock.Mock()
        mock_account_details.currency_code = None
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_size, 2)

    def test_min_bet_size_ac_none(self):
        mock_account_details = None
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_size, 2)

    def test_min_bsp_liability(self):
        mock_account_details = mock.Mock()
        mock_account_details.currency_code = "USD"
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bsp_liability, 20)

    def test_min_bsp_liability_none(self):
        mock_account_details = mock.Mock()
        mock_account_details.currency_code = None
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bsp_liability, 10)

    def test_min_bsp_liability_ac_none(self):
        mock_account_details = None
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bsp_liability, 10)

    def test_min_bet_payout(self):
        mock_account_details = mock.Mock()
        mock_account_details.currency_code = "GBP"
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_payout, 10)

    def test_min_bet_payout_none(self):
        mock_account_details = mock.Mock()
        mock_account_details.currency_code = None
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_payout, 10)

    def test_min_bet_payout_ac_none(self):
        mock_account_details = None
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_payout, 10)


class BacktestClientTest(unittest.TestCase):
    def setUp(self):
        self.backtest_client = BacktestClient()

    def test_login(self):
        self.backtest_client.login()

    def test_keep_alive(self):
        self.backtest_client.keep_alive()

    def test_logout(self):
        self.backtest_client.logout()

    @mock.patch("flumine.clients.backtestclient.AccountDetails")
    def test_update_account_details(self, mock_account_details):
        self.backtest_client.update_account_details()
        self.assertEqual(self.backtest_client.account_details, mock_account_details())

    def test_min_bet_size(self):
        self.backtest_client.update_account_details()
        self.assertEqual(self.backtest_client.min_bet_size, 2)

    def test_min_bsp_liability(self):
        self.backtest_client.update_account_details()
        self.assertEqual(self.backtest_client.min_bsp_liability, 10)

    def test_min_bet_payout(self):
        self.backtest_client.update_account_details()
        self.assertEqual(self.backtest_client.min_bet_payout, 10)
