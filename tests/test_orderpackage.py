import unittest
from unittest import mock

from flumine.order.orderpackage import (
    OrderPackageType,
    BaseOrderPackage,
    EventType,
    QueueType,
    BetfairOrderPackage,
    ExchangeType,
    OrderStatus,
)


class OrderPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_market = mock.Mock()
        self.mock_package_type = mock.Mock()
        self.mock_client = mock.Mock()
        self.mock_order = mock.Mock()
        self.mock_order.status = OrderStatus.PENDING
        self.order_package = BaseOrderPackage(
            self.mock_client,
            "1.234",
            [self.mock_order],
            self.mock_package_type,
            self.mock_market,
        )

    def test_init(self):
        self.assertEqual(self.order_package.client, self.mock_client)
        self.assertEqual(self.order_package.market_id, "1.234")
        self.assertEqual(self.order_package._orders, [self.mock_order])
        self.assertEqual(self.order_package.package_type, self.mock_package_type)
        self.assertEqual(self.order_package.EVENT_TYPE, EventType.ORDER_PACKAGE)
        self.assertEqual(self.order_package.QUEUE_TYPE, QueueType.HANDLER)
        self.assertEqual(self.order_package.market, self.mock_market)
        self.assertIsNone(self.order_package.EXCHANGE)
        self.assertFalse(self.order_package.async_)
        self.assertFalse(self.order_package.processed)

    def test_place_instructions(self):
        with self.assertRaises(NotImplementedError):
            assert self.order_package.place_instructions

    def test_cancel_instructions(self):
        with self.assertRaises(NotImplementedError):
            assert self.order_package.cancel_instructions

    def test_update_instructions(self):
        with self.assertRaises(NotImplementedError):
            assert self.order_package.update_instructions

    def test_replace_instructions(self):
        with self.assertRaises(NotImplementedError):
            assert self.order_package.replace_instructions

    def test_order_limit(self):
        with self.assertRaises(NotImplementedError):
            assert self.order_package.order_limit(OrderPackageType.PLACE)

    def test_orders(self):
        self.assertEqual(self.order_package.orders, [self.mock_order])
        self.order_package._orders = [
            mock.Mock(status=OrderStatus.PENDING),
            mock.Mock(status=OrderStatus.PENDING),
            mock.Mock(status=OrderStatus.VIOLATION),
        ]
        self.assertEqual(len(self.order_package.orders), 2)

    def test_info(self):
        self.assertEqual(
            self.order_package.info,
            {
                "id": self.order_package.id,
                "client": self.order_package.client,
                "market_id": self.order_package.market_id,
                "orders": [self.mock_order.id],
                "package_type": self.order_package.package_type.value,
                "customer_strategy_ref": self.order_package.customer_strategy_ref,
            },
        )

    def test_market_version(self):
        self.assertIsNone(self.order_package.market_version)

    def test_bet_delay(self):
        self.assertEqual(
            self.order_package.bet_delay, self.mock_market.market_book.bet_delay,
        )

    def test_iter(self):
        self.assertEqual([i for i in self.order_package], self.order_package.orders)

    def test_len(self):
        self.assertEqual(len(self.order_package), 1)


class BetfairOrderPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_market = mock.Mock()
        self.mock_package_type = mock.Mock()
        self.mock_client = mock.Mock()
        self.mock_order = mock.Mock()
        self.mock_order.status = OrderStatus.PENDING
        self.order_package = BetfairOrderPackage(
            self.mock_client,
            "1.234",
            [self.mock_order],
            self.mock_package_type,
            self.mock_market,
        )

    def test_init(self):
        self.assertEqual(self.order_package.EXCHANGE, ExchangeType.BETFAIR)

    def test_place_instructions(self):
        self.assertEqual(
            self.order_package.place_instructions,
            [self.mock_order.create_place_instruction()],
        )

    def test_cancel_instructions(self):
        self.assertEqual(
            self.order_package.cancel_instructions,
            [self.mock_order.create_cancel_instruction()],
        )

    def test_update_instructions(self):
        self.assertEqual(
            self.order_package.update_instructions,
            [self.mock_order.create_update_instruction()],
        )

    def test_replace_instructions(self):
        self.assertEqual(
            self.order_package.replace_instructions,
            [self.mock_order.create_replace_instruction()],
        )

    def test_order_limit(self):
        self.assertEqual(self.order_package.order_limit(OrderPackageType.PLACE), 200)
        self.assertEqual(self.order_package.order_limit(OrderPackageType.CANCEL), 60)
        self.assertEqual(self.order_package.order_limit(OrderPackageType.UPDATE), 60)
        self.assertEqual(self.order_package.order_limit(OrderPackageType.REPLACE), 60)
