import unittest
from unittest import mock
from unittest.mock import call

from flumine.execution.transaction import Transaction


class TransactionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_market = mock.Mock()
        self.transaction = Transaction(self.mock_market)

    def test_init(self):
        self.assertEqual(self.transaction.market, self.mock_market)
        self.assertFalse(self.transaction.open)
        self.assertEqual(self.transaction._pending_place, [])
        self.assertEqual(self.transaction._pending_cancel, [])
        self.assertEqual(self.transaction._pending_update, [])
        self.assertEqual(self.transaction._pending_replace, [])

    @mock.patch("flumine.execution.transaction.Transaction.execute")
    def test_enter_exit(self, mock_execute):
        with self.transaction as t:
            self.assertTrue(t.open)
        mock_execute.assert_called()
        self.assertFalse(self.transaction.open)
