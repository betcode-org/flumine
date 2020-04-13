import unittest
from unittest import mock

from flumine.order.orderpackage import (
    BaseOrderPackage,
    EventType,
    QueueType,
    BetfairOrderPackage,
    ExchangeType,
)


class OrderPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_package_type = mock.Mock()
        self.mock_client = mock.Mock()
        self.order_package = BaseOrderPackage(
            self.mock_client, "1.234", [1, 2, 3], self.mock_package_type
        )

    def test_init(self):
        self.assertEqual(self.order_package.client, self.mock_client)
        self.assertEqual(self.order_package.market_id, "1.234")
        self.assertEqual(self.order_package.orders, [1, 2, 3])
        self.assertEqual(self.order_package.package_type, self.mock_package_type)
        self.assertEqual(self.order_package.EVENT_TYPE, EventType.ORDER_PACKAGE)
        self.assertEqual(self.order_package.QUEUE_TYPE, QueueType.HANDLER)
        self.assertIsNone(self.order_package.EXCHANGE)

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

    def test_iter(self):
        self.assertEqual([i for i in self.order_package], self.order_package.orders)

    def test_len(self):
        self.assertEqual(len(self.order_package), 3)


class BetfairOrderPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_package_type = mock.Mock()
        self.mock_client = mock.Mock()
        self.order_package = BetfairOrderPackage(
            self.mock_client, "1.234", [1, 2, 3], self.mock_package_type
        )

    def test_init(self):
        self.assertEqual(self.order_package.EXCHANGE, ExchangeType.BETFAIR)
