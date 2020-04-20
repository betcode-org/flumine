import unittest
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
        self.mock_status = OrderStatus.PENDING
        self.mock_order_type = mock.Mock()
        self.order = BaseOrder(
            self.mock_trade, "BACK", self.mock_order_type, 1, self.mock_status
        )

    def test_init(self):
        self.assertIsNotNone(self.order.id)
        self.assertEqual(self.order.trade, self.mock_trade)
        self.assertEqual(self.order.side, "BACK")
        self.assertEqual(self.order.order_type, self.mock_order_type)
        self.assertEqual(self.order.handicap, 1)
        self.assertEqual(self.order.status, self.mock_status)
        self.assertEqual(self.order.status_log, [self.mock_status])
        self.assertIsNone(self.order.bet_id)
        self.assertIsNone(self.order.EXCHANGE)
        self.assertEqual(self.order._update, {})

    def test__update_status(self):
        self.order._update_status(OrderStatus.LAPSED)
        self.assertEqual(
            self.order.status_log, [OrderStatus.PENDING, OrderStatus.LAPSED]
        )
        self.assertEqual(self.order.status, OrderStatus.LAPSED)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_placing(self, mock__update_status):
        self.order.placing()

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_executable(self, mock__update_status):
        self.order.executable()
        mock__update_status.assert_called_with(OrderStatus.EXECUTABLE)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_execution_complete(self, mock__update_status):
        self.order.execution_complete()
        mock__update_status.assert_called_with(OrderStatus.EXECUTION_COMPLETE)

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

    def test_market_id(self):
        self.assertEqual(self.order.market_id, self.mock_trade.market_id)

    def test_selection_id(self):
        self.assertEqual(self.order.selection_id, self.mock_trade.selection_id)

    def test_lookup(self):
        self.assertEqual(
            self.order.lookup,
            (self.mock_trade.market_id, self.mock_trade.selection_id, 1),
        )

    def test_id_int(self):
        self.assertEqual(self.order.id_int, self.order.id.time)

    def test_info(self):
        self.order.status_log = [OrderStatus.PENDING, OrderStatus.LAPSED]
        self.assertEqual(
            self.order.info,
            {
                "bet_id": None,
                "handicap": 1,
                "id_int": self.order.id_int,
                "market_id": self.mock_trade.market_id,
                "selection_id": self.mock_trade.selection_id,
                "status": self.mock_status.value,
                "status_log": "Pending, Lapsed",
                "trade": self.mock_trade.info,
            },
        )


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

    def test_cancel(self):
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(12)

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.order.cancel(0.01)
        self.assertEqual(self.order._update, {"size_reduction": 0.01})
        self.order.cancel()
        self.assertEqual(self.order._update, {"size_reduction": None})

    def test_update(self):
        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.persistence_type = "LAPSE"
        self.order.update("PERSIST")
        self.assertEqual(self.mock_order_type.persistence_type, "PERSIST")

        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

    def test_replace(self):
        with self.assertRaises(OrderUpdateError):
            self.order.replace(1.01)

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.price = 2.02
        self.order.replace(1.01)
        self.assertEqual(self.order._update, {"new_price": 1.01})

        with self.assertRaises(OrderUpdateError):
            self.order.replace(2.02)

    def test_create_place_instruction(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.assertEqual(
            self.order.create_place_instruction(),
            {
                "customerOrderRef": str(self.order.id_int),
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
                "customerOrderRef": str(self.order.id_int),
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
                "customerOrderRef": str(self.order.id_int),
                "handicap": 0,
                "marketOnCloseOrder": self.mock_order_type.place_instruction(),
                "orderType": "MARKET_ON_CLOSE",
                "selectionId": self.mock_trade.selection_id,
                "side": "BACK",
            },
        )

    def test_create_cancel_instruction(self):
        self.order._update = {"size_reduction": 0.02}
        self.assertEqual(
            self.order.create_cancel_instruction(), {"sizeReduction": 0.02}
        )

    def test_create_update_instruction(self):
        self.mock_order_type.persistence_type = "PERSIST"
        self.assertEqual(
            self.order.create_update_instruction(), {"newPersistenceType": "PERSIST"}
        )

    def test_create_replace_instruction(self):
        self.order._update = {"new_price": 2.02}
        self.assertEqual(self.order.create_replace_instruction(), {"newPrice": 2.02})
