import unittest
from unittest import mock

from flumine.backtest import simulated
from flumine.order.ordertype import OrderTypes


class SimulatedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_order_type = mock.Mock(
            price=12, size=2.00, ORDER_TYPE=OrderTypes.LIMIT
        )
        self.mock_order = mock.Mock(
            selection_id=1234, handicap=1, side="BACK", order_type=self.mock_order_type
        )
        self.simulated = simulated.Simulated(self.mock_order)

    def test_init(self):
        self.assertEqual(self.simulated.order, self.mock_order)
        self.assertEqual(self.simulated.matched, [])

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    @mock.patch("flumine.backtest.simulated.Simulated.take_sp", return_value=True)
    @mock.patch("flumine.backtest.simulated.Simulated._process_traded")
    @mock.patch("flumine.backtest.simulated.Simulated._process_sp")
    def test_call(self, mock__process_sp, mock__process_traded, _, mock__get_runner):
        mock_market_book = mock.Mock()
        mock_market_book.bsp_reconciled = True
        self.simulated(mock_market_book, {})
        mock__process_sp.assert_called_with(mock__get_runner())
        mock__process_traded.assert_called_with(mock__get_runner(), {})

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    @mock.patch("flumine.backtest.simulated.Simulated.take_sp", return_value=True)
    @mock.patch("flumine.backtest.simulated.Simulated._process_traded")
    @mock.patch("flumine.backtest.simulated.Simulated._process_sp")
    def test_call(self, mock__process_sp, mock__process_traded, _, mock__get_runner):
        mock_market_book = mock.Mock()
        mock_market_book.bsp_reconciled = False
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated(mock_market_book, {})
        mock__process_sp.assert_not_called()
        mock__process_traded.assert_not_called()

        mock_market_book.bsp_reconciled = True
        self.simulated(mock_market_book, {})
        mock__process_sp.assert_called_with(mock__get_runner())
        mock__process_traded.assert_not_called()

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit(self, mock__get_runner):
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [mock.Mock(price=12, size=120)]
        mock_runner.ex.available_to_lay = [mock.Mock(price=12, size=120)]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 2)
        self.assertEqual(self.simulated.matched, [(12, 2)])

    def test_place_else(self):
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        mock_market_book = mock.Mock()
        with self.assertRaises(NotImplementedError):
            self.simulated.place(mock_market_book, {}, 1)

    # def test_cancel(self):
    #     pass

    # def test_update(self):
    #     pass

    # def test_replace(self):
    #     pass

    def test__get_runner(self):
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock(selection_id=1234, handicap=1)
        mock_market_book.runners = [mock_runner]
        self.assertEqual(
            self.simulated._get_runner(mock_market_book), mock_runner,
        )
        mock_runner = mock.Mock(selection_id=134, handicap=1)
        mock_market_book.runners = [mock_runner]
        self.assertIsNone(self.simulated._get_runner(mock_market_book))

    @mock.patch(
        "flumine.backtest.simulated.Simulated.side",
        new_callable=mock.PropertyMock,
        return_value="BACK",
    )
    def test__process_price_matched_back(self, mock_side):
        self.simulated._process_price_matched(
            12.0, 2.00, [mock.Mock(price=15, size=120)]
        )
        self.assertEqual(self.simulated.matched, [(15, 2)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            12.0, 2.00, [mock.Mock(price=15, size=1), mock.Mock(price=12, size=1)]
        )
        self.assertEqual(self.simulated.matched, [(15, 1), (12, 1)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            12.0, 2.00, [mock.Mock(price=15, size=1), mock.Mock(price=12, size=0.5)]
        )
        self.assertEqual(self.simulated.matched, [(15, 1), (12, 0.5)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            12.0, 2.00, [mock.Mock(price=15, size=1), mock.Mock(price=11, size=0.5)]
        )
        self.assertEqual(self.simulated.matched, [(15, 1)])

    @mock.patch(
        "flumine.backtest.simulated.Simulated.side",
        new_callable=mock.PropertyMock,
        return_value="LAY",
    )
    def test__process_price_matched_lay(self, mock_side):
        self.simulated._process_price_matched(
            3.0, 20.00, [mock.Mock(price=2.02, size=120)]
        )
        self.assertEqual(self.simulated.matched, [(2.02, 20)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            3.0, 20.00, [mock.Mock(price=2.02, size=1), mock.Mock(price=3, size=20)]
        )
        self.assertEqual(self.simulated.matched, [(2.02, 1), (3, 19)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            3.0, 20.00, [mock.Mock(price=2.02, size=1), mock.Mock(price=2.9, size=0.5)]
        )
        self.assertEqual(self.simulated.matched, [(2.02, 1), (2.9, 0.5)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            3.0, 20.00, [mock.Mock(price=3, size=1), mock.Mock(price=11, size=0.5)]
        )
        self.assertEqual(self.simulated.matched, [(3, 1)])

    def test__process_sp(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated._process_sp(mock_runner)
        self.assertEqual(self.simulated.matched, [(12.2, 2.00)])

    def test__process_sp_none(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = None
        self.simulated._process_sp(mock_runner)
        self.assertEqual(self.simulated.matched, [])

    def test__process_sp_processed(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated.matched = [(12.2, 2)]
        self.simulated._process_sp(mock_runner)
        self.assertEqual(self.simulated.matched, [(12.2, 2)])

    def test__process_sp_processed_semi(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated.matched = [(10.0, 1)]
        self.simulated._process_sp(mock_runner)
        self.assertEqual(self.simulated.matched, [(10.0, 1), (12.2, 1)])

    def test__process_sp_limit_on_close(self):
        mock_limit_on_close_order = mock.Mock(price=10.0, size=2.00, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [(69, 2.00)])

    def test__process_sp_limit_on_close_lay(self):
        mock_limit_on_close_order = mock.Mock(price=100.0, size=2.00, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        self.simulated.order.side = "LAY"
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [(69, 0.03)])

    def test_syn_process_sp_market_on_close(self):
        mock_limit_on_close_order = mock.Mock(size=2.00, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order

        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [(69, 2.00)])

    def test_syn_process_sp_market_on_close_lay(self):
        mock_limit_on_close_order = mock.Mock(size=2.00, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        self.simulated.order.side = "LAY"

        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [(69, 0.03)])

    # def test__process_traded(self):
    #     pass

    def test_wap(self):
        matched = [(1.5, 100), (1.6, 100)]
        assert self.simulated._wap(matched) == (200, 1.55)

    def test_wap_nothing(self):
        matched = []
        assert self.simulated._wap(matched) == (0, 0)

    def test_wap_error(self):
        matched = [(1.5, 0)]
        assert self.simulated._wap(matched) == (0, 0)

    def test_take_sp(self):
        self.assertFalse(self.simulated.take_sp)
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.assertTrue(self.simulated.take_sp)
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.assertTrue(self.simulated.take_sp)
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.simulated.order.order_type.persistence_type = "MARKET_ON_CLOSE"
        self.assertTrue(self.simulated.take_sp)

    def test_side(self):
        self.assertEqual(self.simulated.side, self.mock_order.side)

    def test_average_price_matched(self):
        self.assertEqual(self.simulated.average_price_matched, 0)
        self.simulated.matched = [(1, 2)]
        self.assertEqual(self.simulated.average_price_matched, 1)

    def test_size_matched(self):
        self.assertEqual(self.simulated.size_matched, 0)
        self.simulated.matched = [(1, 2)]
        self.assertEqual(self.simulated.size_matched, 2)

    @mock.patch(
        "flumine.backtest.simulated.Simulated.size_matched",
        new_callable=mock.PropertyMock,
    )
    def test_size_remaining(self, mock_size_matched):
        mock_size_matched.return_value = 0
        self.assertEqual(self.simulated.size_remaining, 2)
        mock_size_matched.return_value = 1
        self.assertEqual(self.simulated.size_remaining, 1)
