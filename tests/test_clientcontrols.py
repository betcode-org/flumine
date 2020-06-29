import unittest
import datetime
from unittest import mock

from flumine.controls.clientcontrols import (
    BaseControl,
    MaxOrderCount,
    OrderPackageType,
)


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
        order_package = mock.Mock()
        self.control(order_package)

        mock_validate.assert_called_with(order_package)

    def test_validate(self):
        with self.assertRaises(NotImplementedError):
            self.control._validate(None)

    def test_on_error(self):
        order = mock.Mock()
        order.info = {"hello": "world"}
        self.control._on_error(order, "test")
        order.violation.assert_called_with()

    def test_on_error_offset(self):
        order = mock.Mock()
        order.info = {"hello": "world"}
        self.control._on_error(order, "test")
        order.violation.assert_called_with()


class TestMaxOrderCount(unittest.TestCase):
    def setUp(self):
        self.mock_client = mock.Mock()
        self.mock_client.transaction_limit = 1000
        self.mock_client.chargeable_transaction_count = 0
        self.mock_flumine = mock.Mock()
        self.trading_control = MaxOrderCount(self.mock_flumine, self.mock_client)

    @mock.patch("flumine.controls.clientcontrols.MaxOrderCount._set_next_hour")
    def test_init(self, mock_set_next_hour):
        self.assertEqual(self.trading_control.client, self.mock_client)
        self.assertEqual(self.trading_control.NAME, "MAX_ORDER_COUNT")
        self.assertEqual(self.trading_control.total, 0)
        self.assertEqual(self.trading_control.place_requests, 0)
        self.assertEqual(self.trading_control.update_requests, 0)
        self.assertEqual(self.trading_control.cancel_requests, 0)
        self.assertEqual(self.trading_control.replace_requests, 0)

        self.assertIsNotNone(self.trading_control._next_hour)
        self.assertEqual(self.trading_control.transaction_count, 0)
        self.assertEqual(self.trading_control.transaction_limit, 1000)

    @mock.patch(
        "flumine.controls.clientcontrols.MaxOrderCount._check_transaction_count"
    )
    @mock.patch("flumine.controls.clientcontrols.MaxOrderCount._check_hour")
    def test_validate_place(self, mock_check_hour, mock__check_transaction_count):
        mock_package = mock.Mock()
        mock_package.package_type = OrderPackageType.PLACE
        mock_package.__len__ = mock.Mock()
        mock_package.__len__.return_value = 1
        self.trading_control._validate(mock_package)

        mock_check_hour.assert_called_with()
        mock__check_transaction_count.assert_called_with(1)
        self.assertEqual(self.trading_control.place_requests, 1)

    @mock.patch("flumine.controls.clientcontrols.MaxOrderCount._check_hour")
    def test_validate_cancel(self, mock_check_hour):
        mock_package = mock.Mock()
        mock_package.package_type = OrderPackageType.CANCEL
        mock_package.__len__ = mock.Mock()
        mock_package.__len__.return_value = 1
        self.trading_control._validate(mock_package)

        mock_check_hour.assert_called_with()
        self.assertEqual(self.trading_control.cancel_requests, 1)

    @mock.patch("flumine.controls.clientcontrols.MaxOrderCount._check_hour")
    def test_validate_update(self, mock_check_hour):
        mock_package = mock.Mock()
        mock_package.package_type = OrderPackageType.UPDATE
        mock_package.__len__ = mock.Mock()
        mock_package.__len__.return_value = 1
        self.trading_control._validate(mock_package)

        mock_check_hour.assert_called_with()
        self.assertEqual(self.trading_control.update_requests, 1)

    @mock.patch("flumine.controls.clientcontrols.MaxOrderCount._check_hour")
    def test_validate_replace(self, mock_check_hour):
        mock_package = mock.Mock()
        mock_package.package_type = OrderPackageType.REPLACE
        mock_package.__len__ = mock.Mock()
        mock_package.__len__.return_value = 1
        self.trading_control._validate(mock_package)

        mock_check_hour.assert_called_with()
        self.assertEqual(self.trading_control.replace_requests, 1)

    @mock.patch("flumine.controls.clientcontrols.MaxOrderCount._set_next_hour")
    def test_check_hour(self, mock_set_next_hour):
        self.trading_control._check_hour()

        self.trading_control.transaction_count = 1069
        now = datetime.datetime.now()
        self.trading_control._next_hour = (now + datetime.timedelta(hours=-1)).replace(
            minute=0, second=0, microsecond=0
        )
        self.trading_control._check_hour()
        mock_set_next_hour.assert_called_with()
        self.assertEqual(self.trading_control.transaction_count, 0)
        self.assertEqual(self.mock_client.chargeable_transaction_count, 69)

    def test_check_transaction_count(self):
        self.trading_control._check_transaction_count(10)
        self.assertEqual(self.trading_control.transaction_count, 10)

    def test_set_next_hour(self):
        self.trading_control._next_hour = None

        self.trading_control._set_next_hour()
        now = datetime.datetime.utcnow()
        now_1 = (now + datetime.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        self.assertEqual(self.trading_control._next_hour, now_1)

    @mock.patch("flumine.controls.clientcontrols.MaxOrderCount._check_hour")
    def test_safe(self, mock_check_hour):
        self.assertTrue(self.trading_control.safe)
        mock_check_hour.assert_called_with()

        self.trading_control.client.transaction_limit = -10
        self.assertFalse(self.trading_control.safe)
        mock_check_hour.assert_called_with()

        self.trading_control.client.transaction_limit = None
        self.assertTrue(self.trading_control.safe)
        mock_check_hour.assert_called_with()

    def test_transaction_limit(self):
        self.assertEqual(
            self.trading_control.transaction_limit, self.mock_client.transaction_limit
        )
