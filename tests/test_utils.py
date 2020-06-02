import logging
import unittest
from unittest import mock

from flumine import utils, FlumineException


class UtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        logging.disable(logging.CRITICAL)

    def test_create_short_uuid(self):
        self.assertTrue(utils.create_short_uuid())

    def test_file_line_count(self):
        self.assertGreater(utils.file_line_count(__file__), 10)

    def test_chunks(self):
        self.assertEqual([i for i in utils.chunks([1, 2, 3], 1)], [[1], [2], [3]])

    def test_create_cheap_hash(self):
        self.assertEqual(
            utils.create_cheap_hash("test"), utils.create_cheap_hash("test"),
        )
        self.assertEqual(len(utils.create_cheap_hash("test", 16)), 16)

    def test_as_dec(self):
        utils.as_dec(2.00)

    # def test_arrange(self):
    #     utils.arange()

    def test_make_prices(self):
        utils.make_prices(utils.MIN_PRICE, utils.CUTOFFS)

    def test_get_price(self):
        self.assertEqual(
            utils.get_price(
                [{"price": 12, "size": 120}, {"price": 34, "size": 120}], 0
            ),
            12,
        )
        self.assertEqual(
            utils.get_price(
                [{"price": 12, "size": 120}, {"price": 34, "size": 120}], 1
            ),
            34,
        )
        self.assertIsNone(
            utils.get_price([{"price": 12, "size": 120}, {"price": 34, "size": 120}], 3)
        )
        self.assertIsNone(utils.get_price([], 3))

    def test_get_size(self):
        self.assertEqual(
            utils.get_size([{"price": 12, "size": 12}, {"price": 34, "size": 34}], 0),
            12,
        )
        self.assertEqual(
            utils.get_size([{"price": 12, "size": 12}, {"price": 34, "size": 34}], 1),
            34,
        )
        self.assertIsNone(
            utils.get_size([{"price": 12, "size": 12}, {"price": 34, "size": 34}], 3)
        )
        self.assertIsNone(utils.get_size([], 3))

    def test_get_sp(self):
        mock_runner = mock.Mock()
        mock_runner.sp = []
        self.assertIsNone(utils.get_sp(mock_runner))
        mock_runner.sp = None
        self.assertIsNone(utils.get_sp(mock_runner))
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = "NaN"
        self.assertIsNone(utils.get_sp(mock_runner))
        mock_runner.sp.actual_sp = 12.2345
        self.assertEqual(utils.get_sp(mock_runner), 12.2345)

    def test_price_ticks_away(self):
        self.assertEqual(utils.price_ticks_away(1.01, 1), 1.02)
        self.assertEqual(utils.price_ticks_away(1.01, 5), 1.06)
        self.assertEqual(utils.price_ticks_away(500, 1), 510)
        self.assertEqual(utils.price_ticks_away(500, -1), 490)
        self.assertEqual(utils.price_ticks_away(1.01, -1), 1.01)
        self.assertEqual(utils.price_ticks_away(1.10, -10), 1.01)
        self.assertEqual(utils.price_ticks_away(1000, 5), 1000)
        with self.assertRaises(ValueError):
            utils.price_ticks_away(999, -1)

    def test_calculate_exposure(self):
        self.assertEqual(utils.calculate_exposure([], []), 0)
        self.assertEqual(utils.calculate_exposure([(0, 0)], [(0, 0), (0, 0)]), 0)
        self.assertEqual(utils.calculate_exposure([(5.6, 2)], []), -2)
        self.assertEqual(utils.calculate_exposure([], [(5.6, 2)]), -9.2)
        self.assertEqual(utils.calculate_exposure([], [(5.6, 2), (5.8, 2)]), -18.8)
        self.assertEqual(utils.calculate_exposure([(5.6, 2)], [(5.6, 2)]), 0)
        self.assertEqual(
            utils.calculate_exposure([(5.6, 2), (100, 20)], [(5.6, 2)]), -20
        )
        self.assertEqual(
            utils.calculate_exposure([(5.6, 2), (100, 20)], [(10, 1000)]), -7010.80
        )
        self.assertEqual(utils.calculate_exposure([(10, 2)], [(5, 2)]), 0)
        self.assertEqual(utils.calculate_exposure([(10, 2)], [(5, 4)]), 2)
        self.assertEqual(utils.calculate_exposure([(10, 2)], [(5, 8)]), -14)

        self.assertEqual(utils.calculate_exposure([(5.6, 200)], [(5.6, 100)]), -100)

    def test_wap(self):
        self.assertEqual(utils.wap([(1.5, 100), (1.6, 100)]), (200, 1.55))
        self.assertEqual(utils.wap([]), (0, 0))
        self.assertEqual(utils.wap([(1.5, 0)]), (0, 0))

    def test_call_check_market(self):
        mock_strategy_check = mock.Mock()
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        utils.call_check_market(mock_strategy_check, mock_market, mock_market_book)
        mock_strategy_check.assert_called_with(mock_market, mock_market_book)

    def test_call_check_market_flumine_error(self):
        mock_strategy_check = mock.Mock(side_effect=FlumineException)
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        self.assertFalse(
            utils.call_check_market(mock_strategy_check, mock_market, mock_market_book)
        )
        mock_strategy_check.assert_called_with(mock_market, mock_market_book)

    def test_call_check_market_error(self):
        mock_strategy_check = mock.Mock(side_effect=ValueError)
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        self.assertFalse(
            utils.call_check_market(mock_strategy_check, mock_market, mock_market_book)
        )
        mock_strategy_check.assert_called_with(mock_market, mock_market_book)

    @mock.patch("flumine.utils.config")
    def test_call_check_market_raise(self, mock_config):
        mock_config.raise_errors = True
        mock_strategy_check = mock.Mock(side_effect=ValueError)
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        with self.assertRaises(ValueError):
            utils.call_check_market(mock_strategy_check, mock_market, mock_market_book)

    def test_call_process_market_book(self):
        mock_strategy = mock.Mock()
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        utils.call_process_market_book(mock_strategy, mock_market, mock_market_book)
        mock_strategy.assert_called_with(mock_market, mock_market_book)

    def test_call_process_market_book_flumine_error(self):
        mock_strategy = mock.Mock(side_effect=FlumineException)
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        utils.call_process_market_book(mock_strategy, mock_market, mock_market_book)
        mock_strategy.assert_called_with(mock_market, mock_market_book)

    def test_call_process_market_book_error(self):
        mock_strategy = mock.Mock(side_effect=ZeroDivisionError)
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        utils.call_process_market_book(mock_strategy, mock_market, mock_market_book)
        mock_strategy.assert_called_with(mock_market, mock_market_book)

    @mock.patch("flumine.utils.config")
    def test_call_process_market_book_raise(self, mock_config):
        mock_config.raise_errors = True
        mock_strategy = mock.Mock(side_effect=ZeroDivisionError)
        mock_market = mock.Mock()
        mock_market_book = mock.Mock()
        with self.assertRaises(ZeroDivisionError):
            utils.call_process_market_book(mock_strategy, mock_market, mock_market_book)
