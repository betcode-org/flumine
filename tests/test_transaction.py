import unittest
from unittest import mock
from unittest.mock import call

from flumine.execution.transaction import Transaction, OrderPackageType
from flumine.exceptions import ControlError, OrderError


class TransactionTest(unittest.TestCase):
    def setUp(self) -> None:
        mock_blotter = {}
        self.mock_market = mock.Mock(blotter=mock_blotter)
        self.transaction = Transaction(self.mock_market, 1, False)

    def test_init(self):
        self.assertEqual(self.transaction.market, self.mock_market)
        self.assertEqual(self.transaction._id, 1)
        self.assertFalse(self.transaction._async_place_orders)
        self.assertFalse(self.transaction._pending_orders)
        self.assertEqual(self.transaction._pending_place, [])
        self.assertEqual(self.transaction._pending_cancel, [])
        self.assertEqual(self.transaction._pending_update, [])
        self.assertEqual(self.transaction._pending_replace, [])

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
            self.transaction.market.market_book.publish_time
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
        self.transaction.market.blotter.has_trade.assert_called_with(
            mock_order.trade.id
        )

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
            self.transaction.market.market_book.publish_time
        )
        self.transaction.market.flumine.log_control.assert_called_with(
            mock_events.TradeEvent()
        )
        mock__validate_controls.assert_not_called()
        self.transaction._pending_place = []
        self.assertFalse(self.transaction._pending_orders)
        self.transaction.market.blotter.has_trade.assert_called_with(
            mock_order.trade.id
        )

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
        mock_order = mock.Mock()
        self.assertTrue(self.transaction.cancel_order(mock_order, 0.01))
        mock_order.cancel.assert_called_with(0.01)
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.CANCEL)
        self.transaction._pending_cancel = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_cancel_order_violation(self, mock__validate_controls):
        mock_order = mock.Mock()
        self.assertFalse(self.transaction.cancel_order(mock_order))
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.CANCEL)
        self.transaction._pending_cancel = []
        self.assertFalse(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_force_cancel_order(self, mock__validate_controls):
        mock_order = mock.Mock()
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
        mock_order = mock.Mock()
        self.assertTrue(self.transaction.update_order(mock_order, "PERSIST"))
        mock_order.update.assert_called_with("PERSIST")
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.UPDATE)
        self.transaction._pending_update = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_update_order_violation(self, mock__validate_controls):
        mock_order = mock.Mock()
        self.assertFalse(self.transaction.update_order(mock_order, "test"))
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.UPDATE)
        self.transaction._pending_update = []
        self.assertFalse(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_force_update_order(self, mock__validate_controls):
        mock_order = mock.Mock()
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
    def test_replace_order(self, mock__validate_controls):
        mock_order = mock.Mock()
        self.assertTrue(self.transaction.replace_order(mock_order, 1.01, 321))
        mock_order.replace.assert_called_with(1.01)
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.REPLACE)
        self.transaction._pending_replace = [(mock_order, None)]
        self.assertTrue(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_replace_order_violation(self, mock__validate_controls):
        mock_order = mock.Mock()
        self.assertFalse(self.transaction.replace_order(mock_order, 2.02))
        mock__validate_controls.assert_called_with(mock_order, OrderPackageType.REPLACE)
        self.transaction._pending_replace = []
        self.assertFalse(self.transaction._pending_orders)

    @mock.patch(
        "flumine.execution.transaction.Transaction._validate_controls",
        return_value=False,
    )
    def test_force_replace_order(self, mock__validate_controls):
        mock_order = mock.Mock()
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
        self.transaction.market.flumine.client.trading_controls = [mock_client_control]
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
        self.transaction.market.flumine.client.trading_controls = [mock_client_control]
        mock_order = mock.Mock()
        mock_package_type = mock.Mock()
        self.assertFalse(
            self.transaction._validate_controls(mock_order, mock_package_type)
        )
        mock_trading_control.assert_called_with(mock_order, mock_package_type)
        mock_client_control.assert_not_called()

    @mock.patch("flumine.execution.transaction.BetfairOrderPackage")
    def test__create_order_package(self, mock_betfair_order_package):
        mock_betfair_order_package.order_limit.return_value = 2
        packages = self.transaction._create_order_package(
            [(1, None), (2, None), (3, 123), (4, 123), (5, 123)], OrderPackageType.PLACE
        )
        mock_betfair_order_package.assert_has_calls(
            [
                call(
                    client=self.transaction.market.flumine.client,
                    market_id=self.transaction.market.market_id,
                    orders=[1, 2],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=None,
                    async_=False,
                ),
                call(
                    client=self.transaction.market.flumine.client,
                    market_id=self.transaction.market.market_id,
                    orders=[3, 4],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=123,
                    async_=False,
                ),
                call(
                    client=self.transaction.market.flumine.client,
                    market_id=self.transaction.market.market_id,
                    orders=[5],
                    package_type=OrderPackageType.PLACE,
                    bet_delay=self.transaction.market.market_book.bet_delay,
                    market_version=123,
                    async_=False,
                ),
            ]
        )
        self.assertEqual(len(packages), 3)
        mock_betfair_order_package.order_limit.assert_called_with(
            OrderPackageType.PLACE
        )

    @mock.patch("flumine.execution.transaction.Transaction.execute")
    def test_enter_exit(self, mock_execute):
        with self.transaction as t:
            self.assertEqual(self.transaction, t)
            t._pending_orders = True
        mock_execute.assert_called()
