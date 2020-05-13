import unittest
import datetime
from unittest import mock

from flumine.order.order import (
    BaseOrder,
    BetfairOrder,
    ExchangeType,
    OrderTypes,
    OrderStatus,
)
from flumine.exceptions import OrderUpdateError


class BaseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_trade = mock.Mock()
        self.mock_order_type = mock.Mock()
        self.order = BaseOrder(self.mock_trade, "BACK", self.mock_order_type, 1)

    def test_init(self):
        self.assertIsNotNone(self.order.id)
        self.assertEqual(self.order.trade, self.mock_trade)
        self.assertEqual(self.order.side, "BACK")
        self.assertEqual(self.order.order_type, self.mock_order_type)
        self.assertEqual(self.order.handicap, 1)
        self.assertIsNone(self.order.runner_status)
        self.assertIsNone(self.order.status)
        self.assertEqual(self.order.status_log, [])
        self.assertIsNone(self.order.bet_id)
        self.assertIsNone(self.order.EXCHANGE)
        self.assertEqual(self.order.update_data, {})

    def test__update_status(self):
        self.order._update_status(OrderStatus.EXECUTION_COMPLETE)
        self.assertEqual(self.order.status_log, [OrderStatus.EXECUTION_COMPLETE])
        self.assertEqual(self.order.status, OrderStatus.EXECUTION_COMPLETE)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_placing(self, mock__update_status):
        self.order.placing()
        mock__update_status.assert_called_with(OrderStatus.PENDING)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_executable(self, mock__update_status):
        self.order.update_data = {123: 456}
        self.order.executable()
        mock__update_status.assert_called_with(OrderStatus.EXECUTABLE)
        self.assertEqual(self.order.update_data, {})

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_execution_complete(self, mock__update_status):
        self.order.update_data = {123: 456}
        self.order.execution_complete()
        mock__update_status.assert_called_with(OrderStatus.EXECUTION_COMPLETE)
        self.assertEqual(self.order.update_data, {})

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_cancelling(self, mock__update_status):
        self.order.cancelling()
        mock__update_status.assert_called_with(OrderStatus.CANCELLING)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_updating(self, mock__update_status):
        self.order.updating()
        mock__update_status.assert_called_with(OrderStatus.UPDATING)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_replacing(self, mock__update_status):
        self.order.replacing()
        mock__update_status.assert_called_with(OrderStatus.REPLACING)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_lapsed(self, mock__update_status):
        self.order.update_data = {123: 456}
        self.order.lapsed()
        mock__update_status.assert_called_with(OrderStatus.LAPSED)
        self.assertEqual(self.order.update_data, {})

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_voided(self, mock__update_status):
        self.order.update_data = {123: 456}
        self.order.voided()
        mock__update_status.assert_called_with(OrderStatus.VOIDED)
        self.assertEqual(self.order.update_data, {})

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_violation(self, mock__update_status):
        self.order.update_data = {123: 456}
        self.order.violation()
        mock__update_status.assert_called_with(OrderStatus.VIOLATION)
        self.assertEqual(self.order.update_data, {})

    def test_place(self):
        with self.assertRaises(NotImplementedError):
            self.order.place()

    def test_cancel(self):
        with self.assertRaises(NotImplementedError):
            self.order.cancel()

    def test_update(self):
        with self.assertRaises(NotImplementedError):
            self.order.update("PERSIST")

    def test_replace(self):
        with self.assertRaises(NotImplementedError):
            self.order.replace(20.0)

    def test_create_place_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order.create_place_instruction()

    def test_create_cancel_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order.create_cancel_instruction()

    def test_create_update_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order.create_update_instruction()

    def test_create_replace_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order.create_replace_instruction()

    def test_update_current_order(self):
        mock_current_order = mock.Mock()
        self.order.update_current_order(mock_current_order)
        self.assertEqual(self.order.responses.current_order, mock_current_order)

    def test_current_order(self):
        self.assertIsNone(self.order.current_order)
        mock_responses = mock.Mock()
        mock_responses.current_order = None
        self.order.responses = mock_responses
        self.assertEqual(self.order.current_order, mock_responses.place_response)
        mock_responses.current_order = 1
        self.assertEqual(self.order.current_order, 1)

    def test_current_order_simulated(self):
        self.order.simulated = True
        self.assertTrue(self.order.current_order)

    def test_average_price_matched(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.average_price_matched

    def test_size_matched(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_matched

    def test_size_remaining(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_remaining

    def test_size_cancelled(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_cancelled

    def test_size_lapsed(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_lapsed

    def test_size_voided(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_voided

    def test_elapsed_seconds(self):
        self.assertIsNone(self.order.elapsed_seconds)
        mock_responses = mock.Mock()
        mock_responses.date_time_placed = datetime.datetime.utcnow()
        self.order.responses = mock_responses
        self.assertGreaterEqual(self.order.elapsed_seconds, 0)

    def test_market_id(self):
        self.assertEqual(self.order.market_id, self.mock_trade.market_id)

    def test_selection_id(self):
        self.assertEqual(self.order.selection_id, self.mock_trade.selection_id)

    def test_lookup(self):
        self.assertEqual(
            self.order.lookup,
            (self.mock_trade.market_id, self.mock_trade.selection_id, 1),
        )

    def test_info(self):
        self.order.status_log = [OrderStatus.PENDING, OrderStatus.EXECUTION_COMPLETE]
        self.assertEqual(
            self.order.info,
            {
                "bet_id": None,
                "handicap": 1,
                "id": self.order.id,
                "market_id": self.mock_trade.market_id,
                "selection_id": self.mock_trade.selection_id,
                "status": None,
                "status_log": "Pending, Execution complete",
                "trade": self.mock_trade.info,
                "customer_order_ref": self.order.customer_order_ref,
            },
        )

    def test_repr(self):
        self.assertEqual(repr(self.order), "Order None: None")


class BetfairOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_trade = mock.Mock()
        self.mock_status = mock.Mock()
        self.mock_order_type = mock.Mock()
        self.order = BetfairOrder(self.mock_trade, "BACK", self.mock_order_type)

    def test_init(self):
        self.assertEqual(self.order.EXCHANGE, ExchangeType.BETFAIR)

    @mock.patch("flumine.order.order.BetfairOrder.placing")
    def test_place(self, mock_placing):
        self.order.place()
        mock_placing.assert_called_with()

    @mock.patch(
        "flumine.order.order.BetfairOrder.size_remaining",
        new_callable=mock.PropertyMock,
    )
    @mock.patch("flumine.order.order.BetfairOrder.cancelling")
    def test_cancel(self, mock_cancelling, mock_size_remaining):
        mock_size_remaining.return_value = 20
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(12)

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.order.cancel(0.01)
        self.assertEqual(self.order.update_data, {"size_reduction": 0.01})
        mock_cancelling.assert_called_with()
        self.order.cancel()
        self.assertEqual(self.order.update_data, {"size_reduction": None})

    @mock.patch(
        "flumine.order.order.BetfairOrder.size_remaining",
        new_callable=mock.PropertyMock,
    )
    @mock.patch("flumine.order.order.BetfairOrder.cancelling")
    def test_cancel_error_size(self, mock_cancelling, mock_size_remaining):
        mock_size_remaining.return_value = 20
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(12)

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(21)

    def test_cancel_error(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.order.status = OrderStatus.PENDING
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(12)

    @mock.patch("flumine.order.order.BetfairOrder.updating")
    def test_update(self, mock_updating):
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.persistence_type = "LAPSE"
        self.order.update("PERSIST")
        self.assertEqual(self.mock_order_type.persistence_type, "PERSIST")
        mock_updating.assert_called_with()

        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

    def test_update_error(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.persistence_type = "LAPSE"
        self.order.status = OrderStatus.PENDING
        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

    @mock.patch("flumine.order.order.BetfairOrder.replacing")
    def test_replace(self, mock_replacing):
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.replace(1.01)

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.price = 2.02
        self.order.replace(1.01)
        self.assertEqual(self.order.update_data, {"new_price": 1.01})
        mock_replacing.assert_called_with()

        with self.assertRaises(OrderUpdateError):
            self.order.replace(2.02)

    def test_replace_error(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.order.status = OrderStatus.PENDING
        with self.assertRaises(OrderUpdateError):
            self.order.replace(1.52)

    def test_create_place_instruction(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.assertEqual(
            self.order.create_place_instruction(),
            {
                "customerOrderRef": self.order.customer_order_ref,
                "handicap": 0,
                "limitOrder": self.mock_order_type.place_instruction(),
                "orderType": "LIMIT",
                "selectionId": self.mock_trade.selection_id,
                "side": "BACK",
            },
        )
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.assertEqual(
            self.order.create_place_instruction(),
            {
                "customerOrderRef": self.order.customer_order_ref,
                "handicap": 0,
                "limitOnCloseOrder": self.mock_order_type.place_instruction(),
                "orderType": "LIMIT_ON_CLOSE",
                "selectionId": self.mock_trade.selection_id,
                "side": "BACK",
            },
        )
        self.mock_order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.assertEqual(
            self.order.create_place_instruction(),
            {
                "customerOrderRef": self.order.customer_order_ref,
                "handicap": 0,
                "marketOnCloseOrder": self.mock_order_type.place_instruction(),
                "orderType": "MARKET_ON_CLOSE",
                "selectionId": self.mock_trade.selection_id,
                "side": "BACK",
            },
        )

    def test_create_cancel_instruction(self):
        self.order.update_data = {"size_reduction": 0.02}
        self.assertEqual(
            self.order.create_cancel_instruction(), {"sizeReduction": 0.02}
        )

    def test_create_update_instruction(self):
        self.mock_order_type.persistence_type = "PERSIST"
        self.assertEqual(
            self.order.create_update_instruction(), {"newPersistenceType": "PERSIST"}
        )

    def test_create_replace_instruction(self):
        self.order.update_data = {"new_price": 2.02}
        self.assertEqual(self.order.create_replace_instruction(), {"newPrice": 2.02})

    def test_average_price_matched(self):
        self.assertEqual(self.order.average_price_matched, 0)
        mock_current_order = mock.Mock(average_price_matched=12.3)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(
            self.order.average_price_matched, mock_current_order.average_price_matched
        )

    def test_size_matched(self):
        self.assertEqual(self.order.size_matched, 0)
        mock_current_order = mock.Mock(size_matched=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_matched, mock_current_order.size_matched)

    def test_size_remaining(self):
        self.assertEqual(self.order.size_remaining, 0)
        mock_current_order = mock.Mock(size_remaining=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_remaining, mock_current_order.size_remaining)

    def test_size_cancelled(self):
        self.assertEqual(self.order.size_cancelled, 0)
        mock_current_order = mock.Mock(size_cancelled=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_cancelled, mock_current_order.size_cancelled)

    def test_size_lapsed(self):
        self.assertEqual(self.order.size_lapsed, 0)
        mock_current_order = mock.Mock(size_lapsed=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_lapsed, mock_current_order.size_lapsed)

    def test_size_voided(self):
        self.assertEqual(self.order.size_voided, 0)
        mock_current_order = mock.Mock(size_voided=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_voided, mock_current_order.size_voided)
