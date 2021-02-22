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
        self.mock_package_type = mock.Mock()
        self.mock_client = mock.Mock()
        self.mock_order = mock.Mock()
        self.mock_order.status = OrderStatus.PENDING
        self.order_package = BaseOrderPackage(
            self.mock_client,
            "1.234",
            [self.mock_order],
            self.mock_package_type,
            1,
            market_version=123,
        )

    def test_init(self):
        self.assertEqual(self.order_package.client, self.mock_client)
        self.assertEqual(self.order_package.market_id, "1.234")
        self.assertEqual(self.order_package._orders, [self.mock_order])
        self.assertEqual(self.order_package.package_type, self.mock_package_type)
        self.assertEqual(self.order_package.EVENT_TYPE, EventType.ORDER_PACKAGE)
        self.assertEqual(self.order_package.QUEUE_TYPE, QueueType.HANDLER)
        self.assertEqual(self.order_package.bet_delay, 1)
        self.assertIsNone(self.order_package.EXCHANGE)
        self.assertFalse(self.order_package.async_)
        self.assertEqual(self.order_package._market_version, 123)
        self.assertFalse(self.order_package.processed)
        self.assertTrue(self.order_package._retry)
        self.assertEqual(self.order_package._max_retries, 3)
        self.assertEqual(self.order_package._retry_count, 0)
        self.assertIsNone(self.order_package.simulated_delay)

    def test_retry(self):
        self.assertTrue(self.order_package.retry())
        self.assertEqual(self.order_package._retry_count, 1)

    @mock.patch("flumine.order.orderpackage.time")
    def test_retry_false_count(self, mock_time):
        self.assertTrue(self.order_package.retry())
        self.assertEqual(self.order_package._retry_count, 1)
        self.assertTrue(self.order_package.retry())
        self.assertEqual(self.order_package._retry_count, 2)
        self.assertTrue(self.order_package.retry())
        self.assertEqual(self.order_package._retry_count, 3)
        self.assertFalse(self.order_package.retry())
        self.assertEqual(self.order_package._retry_count, 3)
        mock_time.sleep.assert_called()

    def test_calc_simulated_delay(self):
        self.assertIsNone(self.order_package.calc_simulated_delay())
        self.order_package.client.execution.EXCHANGE = ExchangeType.SIMULATED
        self.order_package.client.execution.PLACE_LATENCY = 0.1
        self.order_package.client.execution.CANCEL_LATENCY = 0.2
        self.order_package.client.execution.UPDATE_LATENCY = 0.3
        self.order_package.client.execution.REPLACE_LATENCY = 0.4
        self.order_package.package_type = OrderPackageType.PLACE
        self.assertEqual(self.order_package.calc_simulated_delay(), 1.1)
        self.order_package.package_type = OrderPackageType.CANCEL
        self.assertEqual(self.order_package.calc_simulated_delay(), 0.2)
        self.order_package.package_type = OrderPackageType.UPDATE
        self.assertEqual(self.order_package.calc_simulated_delay(), 0.3)
        self.order_package.package_type = OrderPackageType.REPLACE
        self.assertEqual(self.order_package.calc_simulated_delay(), 1.4)

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
                "order_count": 1,
                "package_type": self.order_package.package_type.value,
                "customer_strategy_ref": self.order_package.customer_strategy_ref,
                "bet_delay": self.order_package.bet_delay,
                "market_version": self.order_package._market_version,
                "retry": self.order_package._retry,
                "retry_count": self.order_package._retry_count,
            },
        )

    def test_market_version(self):
        self.assertEqual(
            self.order_package.market_version,
            {"version": self.order_package._market_version},
        )

    def test_iter(self):
        self.assertEqual([i for i in self.order_package], self.order_package.orders)

    def test_len(self):
        self.assertEqual(len(self.order_package), 1)


class BetfairOrderPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_package_type = mock.Mock()
        self.mock_client = mock.Mock()
        self.mock_order = mock.Mock()
        self.mock_order.status = OrderStatus.PENDING
        self.order_package = BetfairOrderPackage(
            self.mock_client,
            "1.234",
            [self.mock_order],
            self.mock_package_type,
            0,
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
