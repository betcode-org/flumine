import unittest
from unittest import mock

from flumine.backtest import utils


class BacktestUtilsTest(unittest.TestCase):
    def test_pending_packages(self):
        mock_package_one = mock.Mock()
        mock_package_one.processed = True
        mock_package_two = mock.Mock()
        mock_package_two.processed = False
        mock_package_three = mock.Mock()
        mock_package_three.processed = False
        pending = utils.PendingPackages()
        pending.append(mock_package_one)
        pending.append(mock_package_two)
        pending.append(mock_package_three)
        self.assertEqual(len(pending), 3)
        self.assertEqual(len([i for i in pending]), 2)
        mock_package_one.processed = False
        self.assertEqual(len([i for i in pending]), 3)
