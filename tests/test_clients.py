import unittest
from unittest import mock
from betfairlightweight.metadata import currency_parameters
from betfairlightweight.exceptions import BetfairError
from betconnect.exceptions import BetConnectException

from flumine.clients.clients import ExchangeType, Clients
from flumine.clients import BaseClient, BetfairClient, SimulatedClient, BetConnectClient
from flumine.clients import betfairclient
from flumine import exceptions


class ClientsTest(unittest.TestCase):
    def setUp(self):
        self.clients = Clients()

    def test_exchange_type(self):
        self.assertEqual(len(ExchangeType), 3)
        assert ExchangeType

    def test_init(self):
        self.assertEqual(self.clients._clients, [])
        self.assertEqual(
            self.clients._exchange_clients,
            {exchange: {} for exchange in ExchangeType},
        )

    def test_add_client(self):
        mock_client = mock.Mock(EXCHANGE=ExchangeType.BETFAIR, username="test")
        self.clients._clients = [mock_client]
        with self.assertRaises(exceptions.ClientError):
            self.clients.add_client(mock_client)

        with self.assertRaises(exceptions.ClientError):
            self.clients.add_client(mock.Mock(EXCHANGE="test", username="test"))

        self.clients._clients = []
        self.clients._exchange_clients[ExchangeType.BETFAIR][
            mock_client.username
        ] = mock_client
        with self.assertRaises(exceptions.ClientError):
            self.clients.add_client(mock_client)

        self.clients._clients = []
        self.clients._exchange_clients = {exchange: {} for exchange in ExchangeType}
        mock_client.EXCHANGE = ExchangeType.BETFAIR
        self.assertEqual(self.clients.add_client(mock_client), mock_client)
        self.assertEqual(self.clients._clients, [mock_client])
        self.assertEqual(
            self.clients._exchange_clients[mock_client.EXCHANGE],
            {mock_client.username: mock_client},
        )

    def test_get_default(self):
        self.clients._clients.append("howlandthehum")
        self.assertEqual(self.clients.get_default(), "howlandthehum")

    def test_get_betfair_default(self):
        mock_client_one = mock.Mock(EXCHANGE=ExchangeType.SIMULATED)
        mock_client_two = mock.Mock(EXCHANGE=ExchangeType.BETFAIR)
        self.clients._clients.append(mock_client_one)
        self.clients._clients.append(mock_client_two)
        self.assertEqual(self.clients.get_betfair_default(), mock_client_two)

    def test_get_client(self):
        self.clients._exchange_clients[ExchangeType.SIMULATED]["joejames"] = 12
        self.assertEqual(
            self.clients.get_client(ExchangeType.SIMULATED, "joejames"), 12
        )

    def test_login(self):
        mock_client = unittest.mock.Mock()
        self.clients._clients = [mock_client]
        self.clients.login()
        mock_client.login.assert_called_with()

    def test_keep_alive(self):
        mock_client = unittest.mock.Mock()
        self.clients._clients = [mock_client]
        self.clients.keep_alive()
        mock_client.keep_alive.assert_called_with()

    def test_logout(self):
        mock_client = unittest.mock.Mock()
        self.clients._clients = [mock_client]
        self.clients.logout()
        mock_client.logout.assert_called_with()

    def test_update_account_details(self):
        mock_client = unittest.mock.Mock()
        self.clients._clients = [mock_client]
        self.clients.update_account_details()
        mock_client.update_account_details.assert_called_with()

    def test_simulated(self):
        self.assertFalse(self.clients.simulated)
        self.clients._clients.append(mock.Mock(paper_trade=True))
        self.assertTrue(self.clients.simulated)

    def test_info(self):
        self.assertEqual(
            self.clients.info, {exchange.value: {} for exchange in ExchangeType}
        )
        mock_client = mock.Mock()
        self.clients._exchange_clients[ExchangeType.BETFAIR]["james"] = mock_client
        self.assertEqual(
            self.clients.info,
            {
                ExchangeType.BETFAIR.value: {"james": mock_client.info},
                ExchangeType.SIMULATED.value: {},
                ExchangeType.BETCONNECT.value: {},
            },
        )

    def test_iter(self):
        for i in self.clients:
            assert i

    def test_len(self):
        self.assertEqual(len(self.clients), 0)


class BaseClientTest(unittest.TestCase):
    def setUp(self):
        self.mock_betting_client = mock.Mock(lightweight=False)
        self.base_client = BaseClient(
            self.mock_betting_client, 1024, 100, 0.02, True, username="test"
        )

    def test_init(self):
        self.assertEqual(self.base_client.betting_client, self.mock_betting_client)
        self.assertEqual(self.base_client.transaction_limit, 1024)
        self.assertEqual(self.base_client.capital_base, 100)
        self.assertEqual(self.base_client.commission_base, 0.02)
        self.assertTrue(self.base_client.interactive_login)
        self.assertEqual(self.base_client._username, "test")
        self.assertIsNone(self.base_client.account_details)
        self.assertIsNone(self.base_client.account_funds)
        self.assertEqual(self.base_client.commission_paid, 0)
        self.assertIsNone(self.base_client.execution)
        self.assertEqual(self.base_client.trading_controls, [])
        self.assertTrue(self.base_client.order_stream)
        self.assertTrue(self.base_client.best_price_execution)
        self.assertTrue(self.base_client.min_bet_validation)
        self.assertFalse(self.base_client.paper_trade)
        self.assertFalse(self.base_client.simulated_full_match)
        self.assertIsNone(self.base_client.execution)

    def test_init_assert(self):
        with self.assertRaises(AssertionError):
            BaseClient(mock.Mock(lightweight=True), 1024, 100, 0.02, True)

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

    def test_add_execution_cls(self):
        mock_flumine = mock.Mock()
        self.base_client.EXCHANGE = ExchangeType.SIMULATED
        mock_execution_cls = mock.Mock()
        self.base_client._execution_cls = mock_execution_cls
        self.base_client.add_execution(mock_flumine)
        self.assertEqual(self.base_client.execution, mock_execution_cls.return_value)
        mock_execution_cls.assert_called_with(mock_flumine)

    def test_add_execution_paper(self):
        self.base_client.paper_trade = True
        self.base_client.EXCHANGE = ExchangeType.BETFAIR
        mock_flumine = mock.Mock()
        self.base_client.add_execution(mock_flumine)
        self.assertEqual(self.base_client.execution, mock_flumine.simulated_execution)

    def test_add_transaction(self):
        mock_trading_control = mock.Mock()
        self.base_client.trading_controls.append(mock_trading_control)
        self.base_client.add_transaction(123, True)
        mock_trading_control.add_transaction.assert_called_with(123, True)

    def test_current_transaction_count_total(self):
        self.assertIsNone(self.base_client.current_transaction_count_total)
        mock_trading_control = mock.Mock(
            NAME="MAX_TRANSACTION_COUNT", current_transaction_count_total=123
        )
        self.base_client.trading_controls.append(mock_trading_control)
        self.assertEqual(self.base_client.current_transaction_count_total, 123)

    def test_transaction_count_total(self):
        self.assertIsNone(self.base_client.transaction_count_total)
        mock_trading_control = mock.Mock(
            NAME="MAX_TRANSACTION_COUNT", transaction_count_total=123
        )
        self.base_client.trading_controls.append(mock_trading_control)
        self.assertEqual(self.base_client.transaction_count_total, 123)

    def test_min_bet_size(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.min_bet_size

    def test_min_bet_payout(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.min_bet_payout

    def test_min_bsp_liability(self):
        with self.assertRaises(NotImplementedError):
            assert self.base_client.min_bsp_liability

    def test_username(self):
        self.assertEqual(
            self.base_client.username, self.base_client.betting_client.username
        )
        self.base_client.betting_client = None
        self.assertEqual(self.base_client.username, self.base_client._username)

    def test_info(self):
        self.assertTrue(self.base_client.info)


class BetfairClientTest(unittest.TestCase):
    def setUp(self):
        self.mock_betting_client = mock.Mock(lightweight=False)
        self.betfair_client = BetfairClient(self.mock_betting_client)

    def test_init(self):
        self.assertEqual(
            betfairclient.MIN_BET_SIZE, currency_parameters["GBP"]["min_bet_size"]
        )
        self.assertEqual(
            betfairclient.MIN_BSP_LIABILITY,
            currency_parameters["GBP"]["min_bsp_liability"],
        )
        self.assertEqual(
            betfairclient.MIN_BET_PAYOUT, currency_parameters["GBP"]["min_bet_payout"]
        )

    def test_login(self):
        self.betfair_client.login()
        self.mock_betting_client.login.assert_called_with()

    def test_login_no_certs(self):
        self.betfair_client.interactive_login = True
        self.betfair_client.login()
        self.mock_betting_client.login_interactive.assert_called_with()

    def test_login_error(self):
        self.betfair_client.betting_client.login.side_effect = BetfairError
        self.assertIsNone(self.betfair_client.login())
        self.mock_betting_client.login.assert_called_with()

    def test_keep_alive(self):
        self.mock_betting_client.session_expired = True
        self.betfair_client.keep_alive()
        self.mock_betting_client.keep_alive.assert_called_with()

    def test_keep_alive_error(self):
        self.betfair_client.betting_client.keep_alive.side_effect = BetfairError
        self.assertIsNone(self.betfair_client.keep_alive())
        self.mock_betting_client.keep_alive.assert_called_with()

    def test_logout(self):
        self.betfair_client.logout()
        self.mock_betting_client.logout.assert_called_with()

    def test_logout_error(self):
        self.betfair_client.betting_client.logout.side_effect = BetfairError
        self.assertIsNone(self.betfair_client.logout())
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

    def test__get_account_details_error(self):
        self.betfair_client.betting_client.account.get_account_details.side_effect = (
            BetfairError
        )
        self.assertIsNone(self.betfair_client._get_account_details())
        self.mock_betting_client.account.get_account_details.assert_called_with()

    def test__get_account_funds(self):
        self.betfair_client._get_account_funds()
        self.mock_betting_client.account.get_account_funds.assert_called_with()

    def test__get_account_funds_error(self):
        self.betfair_client.betting_client.account.get_account_funds.side_effect = (
            BetfairError
        )
        self.assertIsNone(self.betfair_client._get_account_funds())
        self.mock_betting_client.account.get_account_funds.assert_called_with()

    def test_min_bet_size(self):
        mock_account_details = mock.Mock()
        mock_account_details.currency_code = "GBP"
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_size, 1)

    def test_min_bet_size_none(self):
        mock_account_details = mock.Mock()
        mock_account_details.currency_code = None
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_size, 1)

    def test_min_bet_size_ac_none(self):
        mock_account_details = None
        self.betfair_client.account_details = mock_account_details
        self.assertEqual(self.betfair_client.min_bet_size, 1)

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


class SimulatedClientTest(unittest.TestCase):
    def setUp(self):
        self.simulated_client = SimulatedClient()

    def test_login(self):
        self.simulated_client.login()

    def test_keep_alive(self):
        self.simulated_client.keep_alive()

    def test_logout(self):
        self.simulated_client.logout()

    @mock.patch("flumine.clients.simulatedclient.AccountDetails")
    def test_update_account_details(self, mock_account_details):
        self.simulated_client.update_account_details()
        self.assertEqual(self.simulated_client.account_details, mock_account_details())

    def test_min_bet_size(self):
        self.simulated_client.update_account_details()
        self.assertEqual(self.simulated_client.min_bet_size, 1)

    def test_min_bsp_liability(self):
        self.simulated_client.update_account_details()
        self.assertEqual(self.simulated_client.min_bsp_liability, 10)

    def test_min_bet_payout(self):
        self.simulated_client.update_account_details()
        self.assertEqual(self.simulated_client.min_bet_payout, 10)

    def test_username(self):
        self.assertEqual(
            self.simulated_client.username,
            self.simulated_client._username,
        )


class BetConnectClientTest(unittest.TestCase):
    def setUp(self):
        self.mock_betting_client = mock.Mock()
        del self.mock_betting_client.lightweight
        self.betconnect_client = BetConnectClient(self.mock_betting_client)

    def test_login(self):
        self.betconnect_client.login()
        self.mock_betting_client.account.login.assert_called_with()

    def test_login_error(self):
        self.betconnect_client.betting_client.account.login.side_effect = (
            BetConnectException
        )
        self.assertIsNone(self.betconnect_client.login())
        self.mock_betting_client.account.login.assert_called_with()

    def test_keep_alive(self):
        self.mock_betting_client.session_expired = True
        self.betconnect_client.keep_alive()
        self.mock_betting_client.account.refresh_session_token.assert_called_with()

    def test_keep_alive_error(self):
        self.betconnect_client.betting_client.account.refresh_session_token.side_effect = (
            BetConnectException
        )
        self.assertIsNone(self.betconnect_client.keep_alive())
        self.mock_betting_client.account.refresh_session_token.assert_called_with()

    def test_logout(self):
        self.betconnect_client.logout()
        self.mock_betting_client.account.logout.assert_called_with()

    def test_logout_error(self):
        self.betconnect_client.betting_client.account.logout.side_effect = (
            BetConnectException
        )
        self.assertIsNone(self.betconnect_client.logout())
        self.mock_betting_client.account.logout.assert_called_with()

    @mock.patch(
        "flumine.clients.betconnectclient.BetConnectClient._get_account_details"
    )
    @mock.patch("flumine.clients.betconnectclient.BetConnectClient._get_account_funds")
    def test_update_account_details(self, mock_get_funds, mock_get_details):
        self.betconnect_client.update_account_details()
        mock_get_funds.assert_called_with()
        mock_get_details.assert_called_with()
        self.assertEqual(self.betconnect_client.account_details, mock_get_details())
        self.assertEqual(self.betconnect_client.account_funds, mock_get_funds())

    def test__get_account_details(self):
        self.betconnect_client._get_account_details()
        self.mock_betting_client.account.get_user_preferences.assert_called_with()

    def test__get_account_details_error(self):
        self.betconnect_client.betting_client.account.get_user_preferences.side_effect = (
            BetConnectException
        )
        self.assertIsNone(self.betconnect_client._get_account_details())
        self.mock_betting_client.account.get_user_preferences.assert_called_with()

    def test__get_account_funds(self):
        self.betconnect_client._get_account_funds()
        self.mock_betting_client.account.get_balance.assert_called_with()

    def test__get_account_funds_error(self):
        self.betconnect_client.betting_client.account.get_balance.side_effect = (
            BetConnectException
        )
        self.assertIsNone(self.betconnect_client._get_account_funds())
        self.mock_betting_client.account.get_balance.assert_called_with()
