import unittest
import datetime
from unittest import mock

from flumine.controls.clientcontrols import (
    BaseControl,
    MaxTransactionCount,
    OrderPackageType,
)
from flumine.exceptions import ControlError


class TestBaseControl(unittest.TestCase):
    def setUp(self):
        self.mock_flumine = mock.Mock()
        self.mock_client = mock.Mock()
        self.control = BaseControl(self.mock_flumine, self.mock_client)

    def test_init(self):
        self.assertEqual(self.control.flumine, self.mock_flumine)
        self.assertIsNone(self.control.NAME)

    @mock.patch("flumine.controls.BaseControl._validate")
    def test_call(self, mock_validate):
        order = mock.Mock()
        self.control(order, OrderPackageType.PLACE)
        mock_validate.assert_called_with(order, OrderPackageType.PLACE)

    def test_validate(self):
        with self.assertRaises(NotImplementedError):
            self.control._validate(None, None)

    def test_on_error(self):
        order = mock.Mock()
        order.info = {"hello": "world"}
        with self.assertRaises(ControlError):
            self.control._on_error(order, "test")
        order.violation.assert_called_with("Order has violated: None Error: test")


class TestMaxTransactionCount(unittest.TestCase):
    def setUp(self):
        self.mock_client = mock.Mock()
        self.mock_client.transaction_limit = 1000
        self.mock_client.chargeable_transaction_count = 0
        self.mock_flumine = mock.Mock()
        self.trading_control = MaxTransactionCount(self.mock_flumine, self.mock_client)

    def test_init(self):
        self.assertEqual(self.trading_control.client, self.mock_client)
        self.assertEqual(self.trading_control.NAME, "MAX_TRANSACTION_COUNT")
        self.assertIsNone(self.trading_control._next_hour)
        self.assertEqual(self.trading_control.current_transaction_count, 0)
        self.assertEqual(self.trading_control.current_failed_transaction_count, 0)
        self.assertEqual(self.trading_control.transaction_count, 0)
        self.assertEqual(self.trading_control.failed_transaction_count, 0)

    def test_add_transaction(self):
        self.trading_control.add_transaction(123)
        self.assertEqual(self.trading_control.transaction_count, 123)
        self.assertEqual(self.trading_control.current_transaction_count, 123)
        self.trading_control.add_transaction(123, True)
        self.assertEqual(self.trading_control.failed_transaction_count, 123)
        self.assertEqual(self.trading_control.current_failed_transaction_count, 123)
        self.trading_control.add_transaction(123)
        self.assertEqual(self.trading_control.transaction_count, 246)
        self.assertEqual(self.trading_control.current_transaction_count, 246)

    @mock.patch("flumine.controls.clientcontrols.MaxTransactionCount._check_hour")
    def test_validate(self, mock_check_hour):
        mock_order = mock.Mock()
        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_check_hour.assert_called()

    @mock.patch("flumine.controls.clientcontrols.MaxTransactionCount._set_next_hour")
    def test_check_hour(self, mock_set_next_hour):
        self.trading_control._next_hour = datetime.datetime.utcnow()
        self.trading_control._check_hour()

        now = datetime.datetime.now()
        self.trading_control._next_hour = (now + datetime.timedelta(hours=-1)).replace(
            minute=0, second=0, microsecond=0
        )
        self.trading_control._check_hour()
        mock_set_next_hour.assert_called_with()

    @mock.patch("flumine.controls.clientcontrols.MaxTransactionCount._set_next_hour")
    def test_check_hour_none(self, mock_set_next_hour):
        self.trading_control._next_hour = None
        self.trading_control._check_hour()
        mock_set_next_hour.assert_called_with()

    def test_set_next_hour(self):
        self.trading_control.current_transaction_count = 5069
        self.trading_control.current_failed_transaction_count = 5069
        self.trading_control._next_hour = None

        self.trading_control._set_next_hour()
        now = datetime.datetime.utcnow()
        now_1 = (now + datetime.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        self.assertEqual(self.trading_control._next_hour, now_1)
        self.assertEqual(self.trading_control.current_transaction_count, 0)
        self.assertEqual(self.trading_control.current_failed_transaction_count, 0)

    def test_safe(self):
        self.assertTrue(self.trading_control.safe)

        self.trading_control.client.transaction_limit = -10
        self.assertFalse(self.trading_control.safe)

        self.trading_control.client.transaction_limit = None
        self.assertTrue(self.trading_control.safe)

    def test_current_transaction_count_total(self):
        self.trading_control.current_transaction_count = 1
        self.trading_control.current_failed_transaction_count = 2
        self.assertEqual(self.trading_control.current_transaction_count_total, 3)

    def test_transaction_count_total(self):
        self.trading_control.transaction_count = 1
        self.trading_control.failed_transaction_count = 2
        self.assertEqual(self.trading_control.transaction_count_total, 3)

    def test_transaction_limit(self):
        self.assertEqual(
            self.trading_control.transaction_limit, self.mock_client.transaction_limit
        )
