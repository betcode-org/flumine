import unittest
from unittest import mock

from flumine.order.ordertype import (
    ExchangeType,
    OrderTypes,
    BaseOrderType,
    LimitOrder,
    LimitOnCloseOrder,
    MarketOnCloseOrder,
)


class BaseOrderTypeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order_type = BaseOrderType()

    def test_init(self):
        self.assertIsNone(self.order_type.EXCHANGE)
        self.assertIsNone(self.order_type.ORDER_TYPE)

    def test_place_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order_type.place_instruction()


class LimitOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order_type = LimitOrder(1.01, 2, "PERSIST", "YES", 34.5, "NO", 2)

    def test_init(self):
        self.assertEqual(self.order_type.EXCHANGE, ExchangeType.BETFAIR)
        self.assertEqual(self.order_type.ORDER_TYPE, OrderTypes.LIMIT)
        self.assertEqual(self.order_type.price, 1.01)
        self.assertEqual(self.order_type.size, 2)
        self.assertEqual(self.order_type.persistence_type, "PERSIST")
        self.assertEqual(self.order_type.time_in_force, "YES")
        self.assertEqual(self.order_type.min_fill_size, 34.5)
        self.assertEqual(self.order_type.bet_target_type, "NO")
        self.assertEqual(self.order_type.bet_target_size, 2)

    def test_place_instruction(self):
        self.assertEqual(
            self.order_type.place_instruction(),
            {
                "betTargetSize": 2,
                "betTargetType": "NO",
                "minFillSize": 34.5,
                "persistenceType": "PERSIST",
                "price": 1.01,
                "size": 2,
                "timeInForce": "YES",
            },
        )


class LimitOnCloseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order_type = LimitOnCloseOrder(64, 1.01)

    def test_init(self):
        self.assertEqual(self.order_type.EXCHANGE, ExchangeType.BETFAIR)
        self.assertEqual(self.order_type.ORDER_TYPE, OrderTypes.LIMIT_ON_CLOSE)
        self.assertEqual(self.order_type.liability, 64)
        self.assertEqual(self.order_type.price, 1.01)

    def test_place_instruction(self):
        self.assertEqual(
            self.order_type.place_instruction(), {"price": 1.01, "liability": 64}
        )


class MarketOnCloseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order_type = MarketOnCloseOrder(128)

    def test_init(self):
        self.assertEqual(self.order_type.EXCHANGE, ExchangeType.BETFAIR)
        self.assertEqual(self.order_type.ORDER_TYPE, OrderTypes.MARKET_ON_CLOSE)
        self.assertEqual(self.order_type.liability, 128)

    def test_place_instruction(self):
        self.assertEqual(self.order_type.place_instruction(), {"liability": 128})
