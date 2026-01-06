import unittest
from unittest import mock
from unittest.mock import call

from flumine.clients import ExchangeType
from flumine.execution.transaction import Transaction, OrderPackageType
from flumine.exceptions import ControlError, OrderError


class TransactionTest(unittest.TestCase):
    def setUp(self) -> None:
        mock_blotter = {}
        self.mock_market = mock.Mock(blotter=mock_blotter)
        self.mock_client = mock.Mock(trading_controls=[], EXCHANGE=ExchangeType.BETFAIR)
        self.transaction = Transaction(
            self.mock_market, 1, False, self.mock_client, customer_strategy_ref="dotty"
        )

    def test_init(self):
        self.assertEqual(self.transaction.market, self.mock_market)
        self.assertEqual(self.transaction._client, self.mock_client)
        self.assertEqual(self.transaction._id, 1)
        self.assertFalse(self.transaction._async_place_orders)
        self.assertFalse(self.transaction._pending_orders)
        self.assertEqual(self.transaction._pending_place, [])
        self.assertEqual(self.transaction._pending_cancel, [])
        self.assertEqual(self.transaction._pending_update, [])
        self.assertEqual(self.transaction._pending_replace, [])
        self.assertEqual(self.transaction.customer_strategy_ref, "dotty")

    @mock.patch("flumine.execution.transaction.get_market_notes")
    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=True,
    )
    @mock.patch("flumine.execution.transaction.events")
    def test_place_order(
        self, mock_events, mock__validate_controls, mock_get_market_notes
    ):
        self.transaction.market.blotter = mock.MagicMock()
        self.transaction.market.blotter.has_trade.return_value = False
        mock_order = mock.Mock(id="123", lookup=(1, 2, 3))
        mock_order.trade.market_notes = None
        self.assertTrue(self.transaction.place_order(mock_order))
        mock_order.place.assert_called_with(
            self.transaction.market.market_book.publish_time,
            None,
            False,
        )
        self.transaction.market.flumine.log_control.assert_called_with(
            mock_events.TradeEvent()
        )
        mock_get_market_notes.assert_called_with(
            self.mock_market, mock_order.selection_id
        )
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.PLACE)
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.PLACE)
        self.transaction._pending_place = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)
        mock_order.trade.strategy.get_runner_context.assert_called_with(
            *mock_order.lookup
        )
        self.transaction.market.blotter.has_trade.assert_called_with(mock_order.trade)
        mock_order.update_client.assert_called_with(self.transaction._client)

    @mock.patch("flumine.execution.transaction.get_market_notes")
    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=True,
    )
    @mock.patch("flumine.execution.transaction.events")
    def test_place_order_not_executed(
        self, mock_events, mock__validate_controls, mock_get_market_notes
    ):
        self.transaction.market.blotter = mock.MagicMock()
        self.transaction.market.blotter.has_trade.return_value = False
        mock_order = mock.Mock(id="123")
        self.assertTrue(self.transaction.place_order(mock_order, execute=False))
        mock_order.place.assert_called_with(
            self.transaction.market.market_book.publish_time,
            None,
            False,
        )
        self.transaction.market.flumine.log_control.assert_called_with(
            mock_events.TradeEvent()
        )
        mock__validate_controls.assert_not_called()
        self.transaction._pending_place = []
        self.assertFalse(self.transaction._pending_orders)
        self.transaction.market.blotter.has_trade.assert_called_with(mock_order.trade)

    @mock.patch("flumine.execution.transaction.get_market_notes")
    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=True,
    )
    def test_place_order_retry(self, mock__validate_controls, mock_get_market_notes):
        self.transaction.market.blotter = mock.MagicMock()
        self.transaction.market.blotter.has_trade.return_value = False
        self.transaction.market.blotter.__contains__.return_value = True
        mock_order = mock.Mock(lookup=(1, 2, 3))
        with self.assertRaises(OrderError):
            self.transaction.place_order(mock_order)
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.PLACE)
        self.transaction._pending_place = []
        self.assertFalse(self.transaction._pending_orders)
        mock_get_market_notes.assert_not_called()

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_place_order_violation(self, mock__validate_controls):
        mock_order = mock.Mock()
        self.assertFalse(self.transaction.place_order(mock_order))
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.PLACE)
        self.transaction._pending_place = []
        self.assertFalse(self.transaction._pending_orders)

    @mock.patch("flumine.execution.transaction.get_market_notes")
    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    @mock.patch("flumine.execution.transaction.events")
    def test_force_place_order(
        self, mock_events, mock__validate_controls, mock_get_market_notes
    ):
        self.transaction.market.blotter = mock.MagicMock()
        self.transaction.market.blotter.has_trade.return_value = False
        mock_order = mock.Mock(id="123", lookup=(1, 2, 3))
        self.assertTrue(self.transaction.place_order(mock_order, force=True))
        mock__validate_controls.assert_not_called()
        self.transaction._pending_place = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=True,
    )
    def test_cancel_order(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client)
        self.assertTrue(self.transaction.cancel_order(mock_order, 0.01))
        mock_order.cancel.assert_called_with(0.01)
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.CANCEL)
        self.transaction._pending_cancel = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    def test_cancel_order_incorrect_client(self):
        mock_order = mock.Mock(client=123)
        with self.assertRaises(OrderError):
            self.transaction.cancel_order(mock_order, 0.01)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_cancel_order_violation(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client)
        self.assertFalse(self.transaction.cancel_order(mock_order))
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.CANCEL)
        self.transaction._pending_cancel = []
        self.assertFalse(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_force_cancel_order(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client)
        self.assertTrue(self.transaction.cancel_order(mock_order, 0.01, force=True))
        mock_order.cancel.assert_called_with(0.01)
        mock__validate_controls.assert_not_called()
        self.transaction._pending_cancel = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=True,
    )
    def test_update_order(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=ExchangeType.BETFAIR)
        self.assertTrue(self.transaction.update_order(mock_order, "PERSIST"))
        mock_order.update.assert_called_with("PERSIST")
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.UPDATE)
        self.transaction._pending_update = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    def test_update_order_incorrect_client(self):
        mock_order = mock.Mock(client=123, EXCHANGE=ExchangeType.BETFAIR)
        with self.assertRaises(OrderError):
            self.transaction.update_order(mock_order, "PERSIST")

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_update_order_violation(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=ExchangeType.BETFAIR)
        self.assertFalse(self.transaction.update_order(mock_order, "test"))
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.UPDATE)
        self.transaction._pending_update = []
        self.assertFalse(self.transaction._pending_orders)

    def test_update_order_unknown_exchange(self):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=123)
        with self.assertRaises(OrderError):
            self.transaction.update_order(mock_order, "PERSIST", force=True)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_force_update_order(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=ExchangeType.BETFAIR)
        self.assertTrue(
            self.transaction.update_order(mock_order, "PERSIST", force=True)
        )
        mock_order.update.assert_called_with("PERSIST")
        mock__validate_controls.assert_not_called()
        self.transaction._pending_update = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=True,
    )
    def test_update_order_betdaq(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=ExchangeType.BETDAQ)
        self.assertTrue(
            self.transaction.update_order(
                mock_order,
                size_delta=-1,
                new_price=2,
                expected_selection_reset_count=3,
                expected_withdrawal_sequence_number=4,
                cancel_on_in_running=False,
                cancel_if_selection_reset=False,
                set_to_be_sp_if_unmatched=True,
            )
        )
        mock_order.update.assert_called_with(-1, 2, 3, 4, False, False, True)
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.UPDATE)
        self.transaction._pending_update = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=True,
    )
    def test_replace_order(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=ExchangeType.BETFAIR)
        self.assertTrue(self.transaction.replace_order(mock_order, 1.01, 321))
        mock_order.replace.assert_called_with(1.01)
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.REPLACE)
        self.transaction._pending_replace = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    def test_replace_order_incorrect_client(self):
        mock_order = mock.Mock(client=123, EXCHANGE=ExchangeType.BETFAIR)
        with self.assertRaises(OrderError):
            self.transaction.replace_order(mock_order, 1.01, 321)

    def test_replace_order_incorrect_exchange(self):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=123)
        with self.assertRaises(OrderError):
            self.transaction.replace_order(mock_order, 1.01, 321)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_replace_order_violation(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=ExchangeType.BETFAIR)
        self.assertFalse(self.transaction.replace_order(mock_order, 2.02))
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.REPLACE)
        self.transaction._pending_replace = []
        self.assertFalse(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_force_replace_order(self, mock__validate_controls):
        mock_order = mock.Mock(client=self.mock_client, EXCHANGE=ExchangeType.BETFAIR)
        self.assertTrue(
            self.transaction.replace_order(mock_order, 1.01, 321, force=True)
        )
        mock_order.replace.assert_called_with(1.01)
        mock__validate_controls.assert_not_called()
        self.transaction._pending_replace = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    @mock.patch("flumine.execution.transaction.Transaction._create_order_package")
    def test_execute(self, mock__create_order_package):
        self.transaction._pending_orders = True
        mock_package = mock.Mock()
        mock__create_order_package.return_value = [mock_package]
        self.assertEqual(self.transaction.execute(), 0)
        mock_order = mock.Mock()
        self.transaction._pending_place = [(mock_order, 1234)]
        self.transaction._pending_cancel = [(mock_order, None)]
        self.transaction._pending_update = [(mock_order, None)]
        self.transaction._pending_replace = [(mock_order, 1234)]
        self.assertEqual(self.transaction.execute(), 4)
        mock__create_order_package.assert_has_calls(
            [
                call([(mock_order, 1234)], OrderPackageType.PLACE, async_=False),
                call([(mock_order, None)], OrderPackageType.CANCEL),
                call([(mock_order, None)], OrderPackageType.UPDATE),
                call([(mock_order, 1234)], OrderPackageType.REPLACE),
            ]
        )
        self.transaction.market.flumine.process_order_package.assert_has_calls(
            [
                call(mock__create_order_package()[0]),
                call(mock__create_order_package()[0]),
                call(mock__create_order_package()[0]),
                call(mock__create_order_package()[0]),
            ]
        )
        self.assertFalse(self.transaction._pending_orders)

    @mock.patch("flumine.execution.transaction.Transaction._create_order_package")
    def test_execute_async(self, mock__create_order_package):
        self.transaction._pending_orders = True
        self.transaction._async_place_orders = True
        mock_package = mock.Mock()
        mock__create_order_package.return_value = [mock_package]
        self.assertEqual(self.transaction.execute(), 0)
        mock_order = mock.Mock()
        self.transaction._pending_place = [(mock_order, 1234)]
        self.transaction._pending_cancel = [(mock_order, None)]
        self.transaction._pending_update = [(mock_order, None)]
        self.transaction._pending_replace = [(mock_order, 1234)]
        self.assertEqual(self.transaction.execute(), 4)
        mock__create_order_package.assert_has_calls(
            [
                call([(mock_order, 1234)], OrderPackageType.PLACE, async_=True),
                call([(mock_order, None)], OrderPackageType.CANCEL),
                call([(mock_order, None)], OrderPackageType.UPDATE),
                call([(mock_order, 1234)], OrderPackageType.REPLACE),
            ]
        )
        self.transaction.market.flumine.process_order_package.assert_has_calls(
            [
                call(mock__create_order_package()[0]),
                call(mock__create_order_package()[0]),
                call(mock__create_order_package()[0]),
                call(mock__create_order_package()[0]),
            ]
        )
        self.assertFalse(self.transaction._pending_orders)

    def test__validate_controls(self):
        mock_trading_control = mock.Mock()
        mock_client_control = mock.Mock()
        self.transaction.market.flumine.trading_controls = [mock_trading_control]
        self.transaction._client.trading_controls = [mock_client_control]
        mock_order = mock.Mock()
        mock_package_type = mock.Mock()
        self.assertTrue(
            self.transaction._validate_controls(mock_order, mock_package_type)
        )
        mock_trading_control.assert_called_with(mock_order, mock_package_type)
        mock_client_control.assert_called_with(mock_order, mock_package_type)

    def test__validate_controls_violation(self):
        mock_trading_control = mock.Mock()
        mock_trading_control.side_effect = ControlError("test")
        mock_client_control = mock.Mock()
        self.transaction.market.flumine.trading_controls = [mock_trading_control]
        self.transaction._client.trading_controls = [mock_client_control]
        mock_order = mock.Mock()
        mock_package_type = OrderPackageType.CANCEL
        self.assertFalse(
            self.transaction._validate_controls(mock_order, mock_package_type)
        )
        mock_trading_control.assert_called_with(mock_order, mock_package_type)
        mock_client_control.assert_not_called()
        mock_order.executable.assert_called()

    def test__validate_controls_violation_place(self):
        mock_trading_control = mock.Mock()
        mock_trading_control.side_effect = ControlError("test")
        mock_client_control = mock.Mock()
        self.transaction.market.flumine.trading_controls = [mock_trading_control]
        self.transaction._client.trading_controls = [mock_client_control]
        mock_order = mock.Mock()
        mock_package_type = OrderPackageType.PLACE
        self.assertFalse(
            self.transaction._validate_controls(mock_order, mock_package_type)
        )
        mock_trading_control.assert_called_with(mock_order, mock_package_type)
        mock_client_control.assert_not_called()
        mock_order.executable.assert_not_called()

    @mock.patch("flumine.execution.transaction.BetfairOrderPackage")
    def test__create_order_package_betfair(self, mock_betfair_order_package):
        mock_betfair_order_package.order_limit.return_value = 2
        mock_order_one = mock.Mock(id=1, exchange="BETFAIR")
        mock_order_two = mock.Mock(id=2, exchange="BETFAIR")
        mock_order_three = mock.Mock(id=3, exchange="BETFAIR")
        mock_order_four = mock.Mock(id=4, exchange="BETFAIR")
        mock_order_five = mock.Mock(id=5, exchange="BETFAIR")
        packages = self.transaction._create_order_package(
            [
                (mock_order_one, None),
                (mock_order_two, None),
                (mock_order_three, 123),
                (mock_order_four, 123),
                (mock_order_five, 123),
            ],
            OrderPackageType.PLACE,
        )
        self.assertEqual(len(packages), 3)
        mock_betfair_order_package.assert_has_calls(
            [
                call.order_limit(OrderPackageType.PLACE),
                call(
                    client=self.transaction._client,
                    market_id=self.transaction.market.market_id,
                    orders=[mock_order_one, mock_order_two],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=None,
                    async_=False,
                    customer_strategy_ref="dotty",
                ),
                call(
                    client=self.transaction._client,
                    market_id=self.transaction.market.market_id,
                    orders=[mock_order_three, mock_order_four],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=123,
                    async_=False,
                    customer_strategy_ref="dotty",
                ),
                call(
                    client=self.transaction._client,
                    market_id=self.transaction.market.market_id,
                    orders=[mock_order_five],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=123,
                    async_=False,
                    customer_strategy_ref="dotty",
                ),
            ]
        )

    @mock.patch("flumine.execution.transaction.BetfairOrderPackage")
    def test__create_order_package_simulated(self, mock_betfair_order_package):
        self.transaction._client.EXCHANGE = ExchangeType.SIMULATED
        mock_betfair_order_package.order_limit.return_value = 2
        mock_order_one = mock.Mock(id=1, exchange="SIMULATED")
        mock_order_two = mock.Mock(id=2, exchange="SIMULATED")
        mock_order_three = mock.Mock(id=3, exchange="SIMULATED")
        packages = self.transaction._create_order_package(
            [
                (mock_order_one, None),
                (mock_order_two, None),
                (mock_order_three, None),
            ],
            OrderPackageType.PLACE,
        )
        self.assertEqual(len(packages), 2)
        mock_betfair_order_package.assert_has_calls(
            [
                call.order_limit(OrderPackageType.PLACE),
                call(
                    client=self.transaction._client,
                    market_id=self.transaction.market.market_id,
                    orders=[mock_order_one, mock_order_two],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=None,
                    async_=False,
                    customer_strategy_ref="dotty",
                ),
                call(
                    client=self.transaction._client,
                    market_id=self.transaction.market.market_id,
                    orders=[mock_order_three],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=None,
                    async_=False,
                    customer_strategy_ref="dotty",
                ),
            ]
        )

    @mock.patch("flumine.execution.transaction.BetdaqOrderPackage")
    def test__create_order_package_betdaq(self, mock_betdaq_order_package):
        self.transaction._client.EXCHANGE = ExchangeType.BETDAQ
        mock_betdaq_order_package.order_limit.return_value = 2
        mock_order_one = mock.Mock(id=1, exchange="BETDAQ")
        mock_order_two = mock.Mock(id=2, exchange="BETDAQ")
        mock_order_three = mock.Mock(id=3, exchange="BETDAQ")
        packages = self.transaction._create_order_package(
            [
                (mock_order_one, None),
                (mock_order_two, None),
                (mock_order_three, None),
            ],
            OrderPackageType.PLACE,
        )
        self.assertEqual(len(packages), 2)
        mock_betdaq_order_package.assert_has_calls(
            [
                call.order_limit(OrderPackageType.PLACE),
                call(
                    client=self.transaction._client,
                    market_id=self.transaction.market.market_id,
                    orders=[mock_order_one, mock_order_two],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=None,
                    async_=False,
                    customer_strategy_ref="dotty",
                ),
                call(
                    client=self.transaction._client,
                    market_id=self.transaction.market.market_id,
                    orders=[mock_order_three],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=None,
                    async_=False,
                    customer_strategy_ref="dotty",
                ),
            ]
        )

    @mock.patch("flumine.execution.transaction.Transaction.execute")
    def test_enter_exit(self, mock_execute):
        with self.transaction as t:
            self.assertEqual(self.transaction, t)
            t._pending_orders = True
        mock_execute.assert_called()
