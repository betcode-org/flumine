import unittest
from unittest import mock

from flumine.backtest import simulated
from flumine.order.ordertype import OrderTypes


class SimulatedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_order_type = mock.Mock(
            price=12, size=2.00, ORDER_TYPE=OrderTypes.LIMIT
        )
        mock_client = mock.Mock(paper_trade=False)
        mock_trade = mock.Mock(client=mock_client)
        self.mock_order = mock.Mock(
            selection_id=1234,
            handicap=1,
            side="BACK",
            order_type=self.mock_order_type,
            trade=mock_trade,
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
        mock__process_sp.assert_called_with(
            mock_market_book.publish_time_epoch, mock__get_runner()
        )
        mock__process_traded.assert_called_with(
            mock_market_book.publish_time_epoch, mock_runner_analytics.traded
        )

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
        mock__process_sp.assert_called_with(
            mock_market_book.publish_time_epoch, mock__get_runner()
        )
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
        mock_client = mock.Mock(best_price_execution=True)
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 12, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_client, mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 2)
        self.assertEqual(
            self.simulated.matched, [[mock_market_book.publish_time_epoch, 12, 2]]
        )

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_back_unmatched(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
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
        resp = self.simulated.place(mock_client, mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 22)

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_back_bpe(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=False)
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 15, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 16, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_client, mock_market_book, {}, 1)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGE")
        self.assertEqual(self.simulated.matched, [])

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_lay(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 12, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_client, mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 2)
        self.assertEqual(
            self.simulated.matched, [[mock_market_book.publish_time_epoch, 12, 2]]
        )

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_lay_unmatched(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
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
        resp = self.simulated.place(mock_client, mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 22)

    @mock.patch("flumine.backtest.simulated.Simulated._get_runner")
    def test_place_limit_lay_bpe(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=False)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 10, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 10.5, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_client, mock_market_book, {}, 1)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGE")
        self.assertEqual(self.simulated.matched, [])

    def test_place_else(self):
        mock_client = mock.Mock(best_price_execution=True)
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        mock_market_book = mock.Mock()
        self.simulated.place(mock_client, mock_market_book, {}, 1)
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
        self.simulated._process_price_matched(
            1234567, 12.0, 2.00, [{"price": 15, "size": 120}]
        )
        self.assertEqual(self.simulated.matched, [[1234567, 15, 2]])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            1234568, 12.0, 2.00, [{"price": 15, "size": 1}, {"price": 12, "size": 1}]
        )
        self.assertEqual(self.simulated.matched, [[1234568, 15, 1], [1234568, 12, 1]])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            1234569, 12.0, 2.00, [{"price": 15, "size": 1}, {"price": 12, "size": 0.5}]
        )
        self.assertEqual(self.simulated.matched, [[1234569, 15, 1], [1234569, 12, 0.5]])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            1234570, 12.0, 2.00, [{"price": 15, "size": 1}, {"price": 11, "size": 0.5}]
        )
        self.assertEqual(self.simulated.matched, [[1234570, 15, 1]])

    @mock.patch(
        "flumine.backtest.simulated.Simulated.side",
        new_callable=mock.PropertyMock,
        return_value="LAY",
    )
    def test__process_price_matched_lay(self, mock_side):
        self.simulated._process_price_matched(
            1234571, 3.0, 20.00, [{"price": 2.02, "size": 120}]
        )
        self.assertEqual(self.simulated.matched, [[1234571, 2.02, 20]])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            1234571, 3.0, 20.00, [{"price": 2.02, "size": 1}, {"price": 3, "size": 20}]
        )
        self.assertEqual(self.simulated.matched, [[1234571, 2.02, 1], [1234571, 3, 19]])
        self.simulated.matched = []
        self.simulated._process_price_matched(
            1234571,
            3.0,
            20.00,
            [{"price": 2.02, "size": 1}, {"price": 2.9, "size": 0.5}],
        )
        self.assertEqual(
            self.simulated.matched, [[1234571, 2.02, 1], [1234571, 2.9, 0.5]]
        )
        self.simulated.matched = []
        self.simulated._process_price_matched(
            1234571, 3.0, 20.00, [{"price": 3, "size": 1}, {"price": 11, "size": 0.5}]
        )
        self.assertEqual(self.simulated.matched, [[1234571, 3, 1]])

    def test__process_sp(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated._process_sp(1234571, mock_runner)
        self.assertEqual(self.simulated.matched, [[1234571, 12.2, 2.00]])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_none(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = None
        self.simulated._process_sp(1234571, mock_runner)
        self.assertEqual(self.simulated.matched, [])
        self.assertFalse(self.simulated._bsp_reconciled)

    def test__process_sp_processed_semi(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated.matched = [[1234571, 10.0, 1]]
        self.simulated.size_matched = 1
        self.simulated.average_price_matched = 10.0
        self.simulated._process_sp(1234572, mock_runner)
        self.assertEqual(
            self.simulated.matched, [[1234571, 10.0, 1], [1234572, 12.2, 1]]
        )
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_limit_on_close_back(self):
        mock_limit_on_close_order = mock.Mock(price=10.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(1234573, mock_runner_book)
        self.assertEqual(self.simulated.matched, [[1234573, 69, 2.00]])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_limit_on_close_back_no_match(self):
        mock_limit_on_close_order = mock.Mock(price=10.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 8
        self.simulated._process_sp(1234574, mock_runner_book)
        self.assertEqual(self.simulated.matched, [])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_limit_on_close_lay(self):
        mock_limit_on_close_order = mock.Mock(price=100.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        self.simulated.order.side = "LAY"
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(1234575, mock_runner_book)
        self.assertEqual(self.simulated.matched, [[1234575, 69, 0.03]])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_limit_on_close_lay_no_match(self):
        mock_limit_on_close_order = mock.Mock(price=60.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        self.simulated.order.side = "LAY"
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(1234576, mock_runner_book)
        self.assertEqual(self.simulated.matched, [])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_market_on_close_back(self):
        mock_limit_on_close_order = mock.Mock(liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(1234577, mock_runner_book)
        self.assertEqual(self.simulated.matched, [[1234577, 69, 2.00]])
        self.assertTrue(self.simulated._bsp_reconciled)

    def test__process_sp_market_on_close_lay(self):
        mock_limit_on_close_order = mock.Mock(liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        self.simulated.order.side = "LAY"
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(1234578, mock_runner_book)
        self.assertEqual(self.simulated.matched, [[1234578, 69, 0.03]])
        self.assertTrue(self.simulated._bsp_reconciled)

    @mock.patch("flumine.backtest.simulated.Simulated._calculate_process_traded")
    def test__process_traded_back(self, mock__calculate_process_traded):
        self.simulated._process_traded(1234579, {12: 120})
        mock__calculate_process_traded.assert_called_with(1234579, 120)

    @mock.patch("flumine.backtest.simulated.Simulated._calculate_process_traded")
    def test__process_traded_back_no(self, mock__calculate_process_traded):
        self.simulated._process_traded(1234580, {11: 120})
        mock__calculate_process_traded.assert_not_called()

    @mock.patch("flumine.backtest.simulated.Simulated._calculate_process_traded")
    def test__process_traded_lay(self, mock__calculate_process_traded):
        self.simulated.order.side = "LAY"
        self.simulated._process_traded(1234581, {12: 120})
        mock__calculate_process_traded.assert_called_with(1234581, 120)

    @mock.patch("flumine.backtest.simulated.Simulated._calculate_process_traded")
    def test__process_traded_lay_no(self, mock__calculate_process_traded):
        self.simulated.order.side = "LAY"
        self.simulated._process_traded(1234582, {13: 120})
        mock__calculate_process_traded.assert_not_called()

    def test__calculate_process_traded(self):
        self.simulated._calculate_process_traded(1234582, 2.00)
        self.simulated._calculate_process_traded(1234583, 2.00)
        self.simulated._calculate_process_traded(1234584, 2.00)
        self.assertEqual(
            self.simulated.matched, [[1234582, 12, 1.00], [1234583, 12, 1.00]]
        )
        self.assertEqual(self.simulated._piq, 0)

    def test__calculate_process_traded_piq(self):
        self.simulated._piq = 2.00
        self.simulated._calculate_process_traded(1234585, 4.00)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 0)
        self.simulated._calculate_process_traded(1234586, 4.00)
        self.assertEqual(self.simulated.matched, [[1234586, 12, 2.00]])
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
        self.simulated._update_matched([1234, 1, 2])
        self.assertEqual(self.simulated.average_price_matched, 1)

    def test_size_matched(self):
        self.assertEqual(self.simulated.size_matched, 0)
        self.simulated._update_matched([4321, 1, 2])
        self.assertEqual(self.simulated.size_matched, 2)

    def test__update_matched(self):
        self.simulated._update_matched([12345, 10.0, 2.64])
        self.assertEqual(self.simulated.matched, [[12345, 10.0, 2.64]])
        self.assertEqual(self.simulated.size_matched, 2.64)
        self.assertEqual(self.simulated.average_price_matched, 10.0)

    def test_size_remaining(self):
        self.assertEqual(self.simulated.size_remaining, 2)
        self.simulated._update_matched([1234, 1, 1])
        self.assertEqual(self.simulated.size_remaining, 1)

    def test_size_remaining_multi(self):
        self.simulated._update_matched([1234, 1, 0.1])
        self.simulated.size_cancelled = 0.2
        self.simulated.size_lapsed = 0.3
        self.simulated.size_voided = 0.4
        self.assertEqual(self.simulated.size_remaining, 1)

    def test_size_remaining_non_limit(self):
        self.simulated.order.order_type.liability = 2
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.assertEqual(self.simulated.size_remaining, 0)

    def test_profit_back(self):
        self.assertEqual(self.simulated.profit, 0)
        self.simulated.order.runner_status = "WINNER"
        self.simulated._update_matched([1234, 10.0, 2.0])
        self.assertEqual(self.simulated.profit, 18.0)
        self.simulated.order.runner_status = "LOSER"
        self.assertEqual(self.simulated.profit, -2.0)

    def test_profit_lay(self):
        self.simulated.order.side = "LAY"
        self.assertEqual(self.simulated.profit, 0)
        self.simulated.order.runner_status = "WINNER"
        self.simulated._update_matched([1234, 10.0, 2.0])
        self.assertEqual(self.simulated.profit, -18.0)
        self.simulated.order.runner_status = "LOSER"
        self.assertEqual(self.simulated.profit, 2.0)

    def test_bool(self):
        self.assertFalse(self.simulated)
        from flumine import config

        config.simulated = True
        self.assertTrue(self.simulated)
        config.simulated = False

    def test_bool_paper_trade(self):
        self.assertFalse(self.simulated)
        self.simulated.order.trade.client.paper_trade = True
        self.assertTrue(self.simulated)
