import unittest
from unittest import mock

from flumine.order.ordertype import OrderType


class OrderTypeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order_type = OrderType()

    # def test_init(self):
    #     self.assertEqual(self.order_type._strategies, [])
