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
        self.order_package = BaseOrderPackage(self.mock_package_type)

    def test_init(self):
        self.assertEqual(self.order_package.package_type, self.mock_package_type)
        self.assertEqual(self.order_package.EVENT_TYPE, EventType.ORDER_PACKAGE)
        self.assertEqual(self.order_package.QUEUE_TYPE, QueueType.HANDLER)
        self.assertIsNone(self.order_package.EXCHANGE)


class BetfairOrderPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_package_type = mock.Mock()
        self.order_package = BetfairOrderPackage(self.mock_package_type)

    def test_init(self):
        self.assertEqual(self.order_package.EXCHANGE, ExchangeType.BETFAIR)
