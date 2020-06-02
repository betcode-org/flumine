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
        self.assertEqual(self.simulated.size_cancelled, 0)
        self.assertEqual(self.simulated.size_lapsed, 0)
        self.assertEqual(self.simulated.size_voided, 0)
        self.assertEqual(self.simulated._piq, 0)
        self.assertFalse(self.simulated._bsp_reconciled)

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    @mock.patch("flumine.backtest.simulated.Simulated.take_sp", return_value=True)
    @mock.patch("flumine.backtest.simulated.Simulated._process_traded")
    @mock.patch("flumine.backtest.simulated.Simulated._process_sp")
    def test_call(self, mock__process_sp, mock__process_traded, _, mock__get_runner):
        mock_market_book = mock.Mock()
        mock_market_book.bsp_reconciled = True
        mock_runner_analytics = mock.Mock()
        self.simulated(mock_market_book, mock_runner_analytics)
        mock__process_sp.assert_called_with(mock__get_runner())
        mock__process_traded.assert_called_with(mock_runner_analytics.traded)

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    @mock.patch("flumine.backtest.simulated.Simulated.take_sp", return_value=True)
    @mock.patch("flumine.backtest.simulated.Simulated._process_traded")
    @mock.patch("flumine.backtest.simulated.Simulated._process_sp")
    def test_call_not_re(
        self, mock__process_sp, mock__process_traded, _, mock__get_runner
    ):
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
    @mock.patch("flumine.backtest.simulated.Simulated.take_sp", return_value=True)
    @mock.patch("flumine.backtest.simulated.Simulated._process_traded")
    @mock.patch("flumine.backtest.simulated.Simulated._process_sp")
    def test_call_bsp_reconciled(
        self, mock__process_sp, mock__process_traded, _, mock__get_runner
    ):
        self.simulated._bsp_reconciled = True
        mock_market_book = mock.Mock()
        mock_market_book.bsp_reconciled = True
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated(mock_market_book, {})
        mock__process_sp.assert_not_called()
        mock__process_traded.assert_not_called()

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_back(self, mock__get_runner):
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 12, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 2)
        self.assertEqual(self.simulated.matched, [(12, 2)])

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_back_unmatched(self, mock__get_runner):
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 10, "size": 120}]
        mock_runner.ex.available_to_lay = [
            {"price": 10.5, "size": 120},
            {"price": 11.5, "size": 10},
            {"price": 12, "size": 22},
            {"price": 15, "size": 32},
        ]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 22)

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_lay(self, mock__get_runner):
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 12, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 2)
        self.assertEqual(self.simulated.matched, [(12, 2)])

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_lay_unmatched(self, mock__get_runner):
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [
            {"price": 10.5, "size": 120},
            {"price": 11.5, "size": 10},
            {"price": 12, "size": 22},
            {"price": 14, "size": 32},
        ]
        mock_runner.ex.available_to_lay = [{"price": 15, "size": 32}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 22)

    def test_place_else(self):
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        mock_market_book = mock.Mock()
        self.simulated.place(mock_market_book, {}, 1)
        self.assertEqual(self.simulated.matched, [])

    def test__create_place_response(self):
        resp = self.simulated._create_place_response(
            1234, "FAILURE", "dubs of the mad skint and british"
        )
        self.assertEqual(resp.bet_id, "1234")
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "dubs of the mad skint and british")

    def test_cancel(self):
        resp = self.simulated.cancel()
        self.assertEqual(self.simulated.size_cancelled, 2.0)
        self.assertEqual(resp.status, "SUCCESS")
        self.assertEqual(resp.size_cancelled, 2.0)

    def test_cancel_else(self):
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        resp = self.simulated.cancel()
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "BET_ACTION_ERROR")

    def test_update(self):
        resp = self.simulated.update({"newPersistenceType": "PERSIST"})
        self.assertEqual(resp.status, "SUCCESS")

    def test_update_else(self):
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        resp = self.simulated.update({"newPersistenceType": "PERSIST"})
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "BET_ACTION_ERROR")

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
        self.simulated._process_price_matched(12.0, 2.00, [{"price": 15, "size": 120}])
        self.assertEqual(self.simulated.matched, [(15, 2)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            12.0, 2.00, [{"price": 15, "size": 1}, {"price": 12, "size": 1}]
        )
        self.assertEqual(self.simulated.matched, [(15, 1), (12, 1)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            12.0, 2.00, [{"price": 15, "size": 1}, {"price": 12, "size": 0.5}]
        )
        self.assertEqual(self.simulated.matched, [(15, 1), (12, 0.5)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            12.0, 2.00, [{"price": 15, "size": 1}, {"price": 11, "size": 0.5}]
        )
        self.assertEqual(self.simulated.matched, [(15, 1)])

    @mock.patch(
        "flumine.backtest.simulated.Simulated.side",
        new_callable=mock.PropertyMock,
        return_value="LAY",
    )
    def test__process_price_matched_lay(self, mock_side):
        self.simulated._process_price_matched(
            3.0, 20.00, [{"price": 2.02, "size": 120}]
        )
        self.assertEqual(self.simulated.matched, [(2.02, 20)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            3.0, 20.00, [{"price": 2.02, "size": 1}, {"price": 3, "size": 20}]
        )
        self.assertEqual(self.simulated.matched, [(2.02, 1), (3, 19)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            3.0, 20.00, [{"price": 2.02, "size": 1}, {"price": 2.9, "size": 0.5}]
        )
        self.assertEqual(self.simulated.matched, [(2.02, 1), (2.9, 0.5)])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            3.0, 20.00, [{"price": 3, "size": 1}, {"price": 11, "size": 0.5}]
        )
        self.assertEqual(self.simulated.matched, [(3, 1)])

    def test__process_sp(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated._process_sp(mock_runner)
        self.assertEqual(self.simulated.matched, [(12.2, 2.00)])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_none(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = None
        self.simulated._process_sp(mock_runner)
        self.assertEqual(self.simulated.matched, [])
        self.assertFalse(self.simulated._bsp_reconciled)

    def test__process_sp_processed_semi(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated.matched = [(10.0, 1)]
        self.simulated._process_sp(mock_runner)
        self.assertEqual(self.simulated.matched, [(10.0, 1), (12.2, 1)])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_limit_on_close_back(self):
        mock_limit_on_close_order = mock.Mock(price=10.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [(69, 2.00)])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_limit_on_close_back_no_match(self):
        mock_limit_on_close_order = mock.Mock(price=10.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 8
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_limit_on_close_lay(self):
        mock_limit_on_close_order = mock.Mock(price=100.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        self.simulated.order.side = "LAY"
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [(69, 0.03)])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_limit_on_close_lay_no_match(self):
        mock_limit_on_close_order = mock.Mock(price=60.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        self.simulated.order.side = "LAY"
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_market_on_close_back(self):
        mock_limit_on_close_order = mock.Mock(liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [(69, 2.00)])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_market_on_close_lay(self):
        mock_limit_on_close_order = mock.Mock(liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        self.simulated.order.side = "LAY"
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(mock_runner_book)
        self.assertEqual(self.simulated.matched, [(69, 0.03)])
        self.assertTrue(self.simulated._bsp_reconciled)

    @mock.patch("flumine.backtest.simulated.Simulated._calculate_process_traded")
    def test__process_traded_back(self, mock__calculate_process_traded):
        self.simulated._process_traded({12: 120})
        mock__calculate_process_traded.assert_called_with(120)

    @mock.patch("flumine.backtest.simulated.Simulated._calculate_process_traded")
    def test__process_traded_back_no(self, mock__calculate_process_traded):
        self.simulated._process_traded({11: 120})
        mock__calculate_process_traded.assert_not_called()

    @mock.patch("flumine.backtest.simulated.Simulated._calculate_process_traded")
    def test__process_traded_lay(self, mock__calculate_process_traded):
        self.simulated.order.side = "LAY"
        self.simulated._process_traded({12: 120})
        mock__calculate_process_traded.assert_called_with(120)

    @mock.patch("flumine.backtest.simulated.Simulated._calculate_process_traded")
    def test__process_traded_lay_no(self, mock__calculate_process_traded):
        self.simulated.order.side = "LAY"
        self.simulated._process_traded({13: 120})
        mock__calculate_process_traded.assert_not_called()

    def test__calculate_process_traded(self):
        self.simulated._calculate_process_traded(2.00)
        self.simulated._calculate_process_traded(2.00)
        self.simulated._calculate_process_traded(2.00)
        self.assertEqual(self.simulated.matched, [(12, 1.00), (12, 1.00)])
        self.assertEqual(self.simulated._piq, 0)

    def test__calculate_process_traded_piq(self):
        self.simulated._piq = 2.00
        self.simulated._calculate_process_traded(4.00)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 0)
        self.simulated._calculate_process_traded(4.00)
        self.assertEqual(self.simulated.matched, [(12, 2.00)])
        self.assertEqual(self.simulated._piq, 0)

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

    @mock.patch(
        "flumine.backtest.simulated.Simulated.size_matched",
        new_callable=mock.PropertyMock,
    )
    def test_size_remaining_multi(self, mock_size_matched):
        mock_size_matched.return_value = 0.1
        self.simulated.size_cancelled = 0.2
        self.simulated.size_lapsed = 0.3
        self.simulated.size_voided = 0.4
        self.assertEqual(self.simulated.size_remaining, 1)

    def test_size_remaining_non_limit(self):
        self.simulated.order.order_type.liability = 2
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.assertEqual(self.simulated.size_remaining, 0)

    @mock.patch(
        "flumine.backtest.simulated.Simulated.average_price_matched",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "flumine.backtest.simulated.Simulated.size_matched",
        new_callable=mock.PropertyMock,
    )
    def test_profit_back(self, mock_size_matched, mock_average_price_matched):
        self.assertEqual(self.simulated.profit, 0)
        self.simulated.order.runner_status = "WINNER"
        mock_size_matched.return_value = 2.00
        mock_average_price_matched.return_value = 10.0
        self.assertEqual(self.simulated.profit, 18.0)
        self.simulated.order.runner_status = "LOSER"
        self.assertEqual(self.simulated.profit, -2.0)

    @mock.patch(
        "flumine.backtest.simulated.Simulated.average_price_matched",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "flumine.backtest.simulated.Simulated.size_matched",
        new_callable=mock.PropertyMock,
    )
    def test_profit_back(self, mock_size_matched, mock_average_price_matched):
        self.simulated.order.side = "LAY"
        self.assertEqual(self.simulated.profit, 0)
        self.simulated.order.runner_status = "WINNER"
        mock_size_matched.return_value = 2.00
        mock_average_price_matched.return_value = 10.0
        self.assertEqual(self.simulated.profit, -18.0)
        self.simulated.order.runner_status = "LOSER"
        self.assertEqual(self.simulated.profit, 2.0)

    def test_bool(self):
        self.assertFalse(self.simulated)
        from flumine import config

        config.simulated = True
        self.assertTrue(self.simulated)
