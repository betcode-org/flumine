import unittest
from unittest import mock

from flumine.simulation import simulatedorder
from flumine.order.ordertype import OrderTypes

EXECUTION_COMPLETE = "EXECUTION_COMPLETE"


class SimulatedOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_order_type = mock.Mock(
            price=12, size=2.00, ORDER_TYPE=OrderTypes.LIMIT
        )
        mock_client = mock.Mock(
            paper_trade=False, min_bsp_liability=10, simulated_full_match=False
        )
        mock_trade = mock.Mock()
        self.mock_order = mock.Mock(
            selection_id=1234,
            handicap=1,
            side="BACK",
            order_type=self.mock_order_type,
            trade=mock_trade,
            number_of_dead_heat_winners=None,
            client=mock_client,
        )
        self.simulated = simulatedorder.SimulatedOrder(self.mock_order)

    def test_init(self):
        self.assertEqual(self.simulated.order, self.mock_order)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_cancelled, 0)
        self.assertEqual(self.simulated.size_lapsed, 0)
        self.assertEqual(self.simulated.size_voided, 0)
        self.assertEqual(self.simulated._piq, 0)
        self.assertIsNone(self.simulated.market_version)
        self.assertFalse(self.simulated._bsp_reconciled)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.take_sp", return_value=True
    )
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_traded")
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_sp")
    def test_call_process_traded(
        self, mock__process_sp, mock__process_traded, _, mock__get_runner
    ):
        mock_market_book = mock.Mock(bsp_reconciled=False)
        traded = {1: 2}
        self.simulated(mock_market_book, traded)
        mock__process_sp.assert_not_called()
        mock__process_traded.assert_called_with(
            mock_market_book.publish_time_epoch, traded
        )

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.take_sp", return_value=True
    )
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_traded")
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_sp")
    def test_call_process_sp(
        self, mock__process_sp, mock__process_traded, _, mock__get_runner
    ):
        mock_market_book = mock.Mock()
        mock_market_book.bsp_reconciled = True
        mock_runner_analytics = mock.Mock()
        self.simulated(mock_market_book, mock_runner_analytics)
        mock__process_sp.assert_called_with(
            mock_market_book.publish_time_epoch, mock__get_runner()
        )
        mock__process_traded.assert_not_called()

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.take_sp", return_value=True
    )
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_traded")
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_sp")
    def test_call_market_version(
        self, mock__process_sp, mock__process_traded, _, mock__get_runner
    ):
        self.simulated.market_version = 123
        self.simulated.order.order_type.persistence_type = "LAPSE"
        mock_market_book = mock.Mock(
            bsp_reconciled=False, version=124, status="SUSPENDED"
        )
        mock_runner_analytics = mock.Mock()
        self.simulated(mock_market_book, mock_runner_analytics)
        self.assertEqual(self.simulated.size_lapsed, 2.0)
        self.assertEqual(self.simulated.size_remaining, 0.0)
        mock__process_sp.assert_not_called()
        mock__process_traded.assert_not_called()

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.take_sp", return_value=True
    )
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_traded")
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_sp")
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

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.take_sp", return_value=True
    )
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_traded")
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._process_sp")
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

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 12, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(self.simulated.market_version, mock_market_book.version)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 2)
        self.assertEqual(
            self.simulated.matched, [[mock_market_book.publish_time_epoch, 12, 2]]
        )

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_target_size(self, mock__get_runner):
        self.mock_order.order_type.size = None
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 12, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        with self.assertRaises(NotImplementedError):
            self.simulated.place(mock_order_package, mock_market_book, {}, 1)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_fill_or_kill_matched(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 12, "size": 1}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL"}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(self.simulated.market_version, mock_market_book.version)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 1)
        self.assertEqual(
            self.simulated.matched, [[mock_market_book.publish_time_epoch, 12, 1]]
        )
        self.assertEqual(self.simulated.size_lapsed, 1)
        self.assertEqual(self.simulated.size_remaining, 0)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_fill_or_kill_lapsed(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 1}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL"}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(self.simulated.market_version, mock_market_book.version)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 2)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_fill_or_kill_no_price(self, mock__get_runner):
        self.mock_order.order_type.price = 1.01
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = []
        mock_runner.ex.available_to_lay = []
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL"}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(self.simulated.market_version, mock_market_book.version)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 2)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_fill_or_kill_min_fill_size_matched(
        self, mock__get_runner
    ):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 12, "size": 1}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL", "minFillSize": 1}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(self.simulated.market_version, mock_market_book.version)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 1)
        self.assertEqual(
            self.simulated.matched, [[mock_market_book.publish_time_epoch, 12, 1]]
        )
        self.assertEqual(self.simulated.size_lapsed, 1)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_fill_or_kill_min_fill_size_lapsed(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 12, "size": 1}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        instruction = {
            "limitOrder": {"timeInForce": "FILL_OR_KILL", "minFillSize": 1.01}
        }
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(self.simulated.market_version, mock_market_book.version)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 2)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_fill_or_kill_vwap(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        self.mock_order.order_type.size = 4
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [
            {"price": 13, "size": 1},
            {"price": 12, "size": 1},
            {"price": 11, "size": 1},
        ]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 120}]
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL"}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(self.simulated.market_version, mock_market_book.version)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 3)
        self.assertEqual(
            self.simulated.matched,
            [
                [mock_market_book.publish_time_epoch, 13, 1],
                [mock_market_book.publish_time_epoch, 12, 1],
                [mock_market_book.publish_time_epoch, 11, 1],
            ],
        )
        self.assertEqual(self.simulated.size_lapsed, 1)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_market_status(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=False)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="SUSPENDED")
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "ERROR_IN_ORDER")
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_voided, 2)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_market_version(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=False)
        mock_order_package = mock.Mock(
            client=mock_client, market_version={"version": 123}
        )
        mock_market_book = mock.Mock(status="OPEN", version=124)
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "ERROR_IN_ORDER")
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_voided, 2)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_unmatched(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 10, "size": 120}]
        mock_runner.ex.available_to_lay = [
            {"price": 10.5, "size": 120},
            {"price": 11.5, "size": 10},
            {"price": 12, "size": 22},
            {"price": 15, "size": 32},
        ]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 22)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_back_bpe(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=False)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 15, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 16, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGE")
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 2)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 12, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 2)
        self.assertEqual(
            self.simulated.matched, [[mock_market_book.publish_time_epoch, 12, 2]]
        )

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay_fill_or_kill_matched(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 12, "size": 1}]
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL"}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 1)
        self.assertEqual(
            self.simulated.matched, [[mock_market_book.publish_time_epoch, 12, 1]]
        )
        self.assertEqual(self.simulated.size_lapsed, 1)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay_fill_or_kill_lapsed(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 13, "size": 1}]
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL"}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 2)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay_fill_or_kill_no_price(self, mock__get_runner):
        self.mock_order.order_type.price = 1000
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = []
        mock_runner.ex.available_to_lay = []
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL"}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 2)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay_fill_or_kill_min_fill_size_matched(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 12, "size": 1}]
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL", "minFillSize": 1}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 1)
        self.assertEqual(
            self.simulated.matched, [[mock_market_book.publish_time_epoch, 12, 1]]
        )
        self.assertEqual(self.simulated.size_lapsed, 1)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay_fill_or_kill_min_fill_size_lapsed(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 12, "size": 1}]
        mock__get_runner.return_value = mock_runner
        instruction = {
            "limitOrder": {"timeInForce": "FILL_OR_KILL", "minFillSize": 1.01}
        }
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 2)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay_fill_or_kill_vwap(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        self.mock_order.order_type.size = 4
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 11, "size": 120}]
        mock_runner.ex.available_to_lay = [
            {"price": 11, "size": 1},
            {"price": 12, "size": 1},
            {"price": 13, "size": 1},
        ]
        mock__get_runner.return_value = mock_runner
        instruction = {"limitOrder": {"timeInForce": "FILL_OR_KILL"}}
        resp = self.simulated.place(
            mock_order_package, mock_market_book, instruction, 1
        )
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 3)
        self.assertEqual(
            self.simulated.matched,
            [
                [mock_market_book.publish_time_epoch, 11, 1],
                [mock_market_book.publish_time_epoch, 12, 1],
                [mock_market_book.publish_time_epoch, 13, 1],
            ],
        )
        self.assertEqual(self.simulated.size_lapsed, 1)
        self.assertEqual(self.simulated.size_remaining, 0)
        self.assertEqual(self.simulated.status, EXECUTION_COMPLETE)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay_unmatched(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [
            {"price": 10.5, "size": 120},
            {"price": 11.5, "size": 10},
            {"price": 12, "size": 22},
            {"price": 14, "size": 32},
        ]
        mock_runner.ex.available_to_lay = [{"price": 15, "size": 32}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 22)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_lay_bpe(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=False)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "LAY"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 10, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 10.5, "size": 120}]
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGE")
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 2)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_limit_removed_runner(self, mock__get_runner):
        mock_client = mock.Mock(best_price_execution=False)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.side = "BACK"
        mock_market_book = mock.Mock(status="OPEN")
        mock_runner = mock.Mock()
        mock_runner.ex.available_to_back = [{"price": 10, "size": 120}]
        mock_runner.ex.available_to_lay = [{"price": 10.5, "size": 120}]
        mock_runner.status = "REMOVED"
        mock__get_runner.return_value = mock_runner
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "RUNNER_REMOVED")
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_voided, 2)

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder._create_place_response"
    )
    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_else(self, mock__get_runner, mock__create_place_response):
        mock__get_runner.status = "ACTIVE"
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        mock_market_book = mock.Mock(status="OPEN")
        self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(self.simulated.matched, [])
        mock__create_place_response.assert_called_with(1)

    @mock.patch("flumine.simulation.simulatedorder.SimulatedOrder._get_runner")
    def test_place_else_bsp_recon(self, mock__get_runner):
        mock__get_runner.status = "ACTIVE"
        mock_client = mock.Mock(best_price_execution=True)
        mock_order_package = mock.Mock(client=mock_client, market_version=None)
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        mock_market_book = mock.Mock(status="OPEN", bsp_reconciled=True, inplay=False)
        resp = self.simulated.place(mock_order_package, mock_market_book, {}, 1)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "MARKET_NOT_OPEN_FOR_BSP_BETTING")
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_voided, 0)

    def test__create_place_response(self):
        resp = self.simulated._create_place_response(
            1234, "FAILURE", error_code="dubs of the mad skint and british"
        )
        self.assertEqual(resp.bet_id, "1234")
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.order_status, "EXECUTABLE")
        self.assertEqual(resp.error_code, "dubs of the mad skint and british")

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.size_remaining",
        new_callable=mock.PropertyMock,
        return_value=0,
    )
    def test__create_place_response_complete(self, mock_size_remaining):
        resp = self.simulated._create_place_response(1234)
        self.assertEqual(resp.bet_id, "1234")
        self.assertEqual(resp.status, "SUCCESS")
        self.assertEqual(resp.order_status, "EXECUTION_COMPLETE")

    def test__create_place_response_full_match(self):
        self.mock_order.client.simulated_full_match = True
        resp = self.simulated._create_place_response(1234)
        self.assertEqual(resp.average_price_matched, 12)
        self.assertEqual(resp.size_matched, 2)
        self.assertEqual(self.simulated.matched, [[0, 12, 2.0]])
        self.assertEqual(self.simulated.size_matched, 2)
        self.assertEqual(self.simulated.average_price_matched, 12)
        self.assertEqual(resp.bet_id, "1234")
        self.assertEqual(resp.status, "SUCCESS")
        self.assertEqual(resp.order_status, "EXECUTION_COMPLETE")

    def test__create_place_response_failure_full_match(self):
        self.mock_order.client.simulated_full_match = True
        resp = self.simulated._create_place_response(None, status="FAILURE")
        self.assertEqual(resp.average_price_matched, 0)
        self.assertEqual(resp.size_matched, 0)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_matched, 0)
        self.assertEqual(self.simulated.average_price_matched, 0)
        self.assertIsNone(resp.bet_id)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.order_status, "EXECUTABLE")

    def test_cancel(self):
        self.simulated.order.update_data = {}
        mock_market_book = mock.Mock(status="OPEN")
        resp = self.simulated.cancel(mock_market_book)
        self.assertEqual(self.simulated.size_cancelled, 2.0)
        self.assertEqual(resp.status, "SUCCESS")
        self.assertEqual(resp.size_cancelled, 2.0)

    def test_cancel_market_status(self):
        mock_market_book = mock.Mock(status="SUSPENDED")
        resp = self.simulated.cancel(mock_market_book)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "ERROR_IN_ORDER")
        self.assertEqual(self.simulated.size_cancelled, 0)

    def test_cancel_reduction(self):
        self.simulated.order.update_data = {"size_reduction": 0.50}
        mock_market_book = mock.Mock(status="OPEN")
        resp = self.simulated.cancel(mock_market_book)
        self.assertEqual(self.simulated.size_cancelled, 0.50)
        self.assertEqual(self.simulated.size_remaining, 1.50)
        self.assertEqual(resp.status, "SUCCESS")
        self.assertEqual(resp.size_cancelled, 0.50)

    def test_cancel_reduction_multi(self):
        self.simulated.size_cancelled = 0.10
        self.simulated.order.update_data = {"size_reduction": 0.50}
        mock_market_book = mock.Mock(status="OPEN")
        resp = self.simulated.cancel(mock_market_book)
        self.assertEqual(self.simulated.size_cancelled, 0.60)
        self.assertEqual(self.simulated.size_remaining, 1.40)
        self.assertEqual(resp.status, "SUCCESS")
        self.assertEqual(resp.size_cancelled, 0.50)

    def test_cancel_reduction_greater_than(self):
        self.simulated.order.update_data = {"size_reduction": 64.0}
        mock_market_book = mock.Mock(status="OPEN")
        resp = self.simulated.cancel(mock_market_book)
        self.assertEqual(self.simulated.size_cancelled, 2.00)
        self.assertEqual(self.simulated.size_remaining, 0.00)
        self.assertEqual(resp.status, "SUCCESS")
        self.assertEqual(resp.size_cancelled, 2.00)

    def test_cancel_else(self):
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        mock_market_book = mock.Mock(status="OPEN")
        resp = self.simulated.cancel(mock_market_book)
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "BET_ACTION_ERROR")

    def test_update(self):
        mock_market_book = mock.Mock(status="OPEN")
        resp = self.simulated.update(
            mock_market_book, {"newPersistenceType": "PERSIST"}
        )
        self.assertEqual(resp.status, "SUCCESS")
        self.assertEqual(self.simulated.order.order_type.persistence_type, "PERSIST")

    def test_update_market_status(self):
        mock_market_book = mock.Mock(status="SUSPENDED")
        resp = self.simulated.update(
            mock_market_book, {"newPersistenceType": "PERSIST"}
        )
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "ERROR_IN_ORDER")

    def test_update_market_p_enabled(self):
        mock_market_book = mock.Mock(status="OPEN")
        mock_market_book.market_definition.persistence_enabled = False
        resp = self.simulated.update(
            mock_market_book, {"newPersistenceType": "PERSIST"}
        )
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "INVALID_PERSISTENCE_TYPE")

    def test_update_else(self):
        mock_market_book = mock.Mock(status="OPEN")
        self.simulated.order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        resp = self.simulated.update(
            mock_market_book, {"newPersistenceType": "PERSIST"}
        )
        self.assertEqual(resp.status, "FAILURE")
        self.assertEqual(resp.error_code, "BET_ACTION_ERROR")

    def test__get_runner(self):
        mock_market_book = mock.Mock()
        mock_runner = mock.Mock(selection_id=1234, handicap=1)
        mock_market_book.runners = [mock_runner]
        self.assertEqual(
            self.simulated._get_runner(mock_market_book),
            mock_runner,
        )
        mock_runner = mock.Mock(selection_id=134, handicap=1)
        mock_market_book.runners = [mock_runner]
        self.assertIsNone(self.simulated._get_runner(mock_market_book))

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.side",
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
        "flumine.simulation.simulatedorder.SimulatedOrder.side",
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

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.side",
        new_callable=mock.PropertyMock,
        return_value="BACK",
    )
    def test__process_price_matched_vwap_back(self, mock_side):
        self.simulated._process_price_matched_vwap(
            1234567, 12.0, 2.00, [{"price": 15, "size": 120}], 2
        )
        self.assertEqual(self.simulated.matched, [[1234567, 15, 2]])
        self.simulated.matched = []
        self.simulated._process_price_matched_vwap(
            1234567,
            12.0,
            3.00,
            [
                {"price": 13, "size": 1},
                {"price": 12, "size": 1},
                {"price": 11, "size": 1},
            ],
            3,
        )
        self.assertEqual(
            self.simulated.matched,
            [[1234567, 13, 1], [1234567, 12, 1], [1234567, 11, 1]],
        )
        self.simulated.matched = []
        self.simulated.order.order_type.size = 5
        self.simulated._process_price_matched_vwap(
            1234567,
            12.0,
            5.00,
            [
                {"price": 13, "size": 1},
                {"price": 12, "size": 1},
                {"price": 11, "size": 1},
            ],
            5,
        )
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 5)
        self.simulated.matched = []
        self.simulated._process_price_matched_vwap(
            1234567,
            12.0,
            5.00,
            [
                {"price": 13, "size": 1},
                {"price": 12, "size": 1},
                {"price": 11, "size": 1},
            ],
            3,
        )
        self.assertEqual(
            self.simulated.matched,
            [[1234567, 13, 1], [1234567, 12, 1], [1234567, 11, 1]],
        )

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.side",
        new_callable=mock.PropertyMock,
        return_value="LAY",
    )
    def test__process_price_matched_vwap_lay(self, mock_side):
        self.simulated._process_price_matched_vwap(
            1234567, 12.0, 2.00, [{"price": 11, "size": 120}], 2
        )
        self.assertEqual(self.simulated.matched, [[1234567, 11, 2]])
        self.simulated.matched = []
        self.simulated._process_price_matched_vwap(
            1234567,
            12.0,
            3.00,
            [
                {"price": 11, "size": 1},
                {"price": 12, "size": 1},
                {"price": 13, "size": 1},
            ],
            3,
        )
        self.assertEqual(
            self.simulated.matched,
            [[1234567, 11, 1], [1234567, 12, 1], [1234567, 13, 1]],
        )
        self.simulated.matched = []
        self.simulated.order.order_type.size = 5
        self.simulated._process_price_matched_vwap(
            1234567,
            12.0,
            5.00,
            [
                {"price": 11, "size": 1},
                {"price": 12, "size": 1},
                {"price": 13, "size": 1},
            ],
            5,
        )
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 5)
        self.simulated.matched = []
        self.simulated._process_price_matched_vwap(
            1234567,
            12.0,
            5.00,
            [
                {"price": 11, "size": 1},
                {"price": 12, "size": 1},
                {"price": 13, "size": 1},
            ],
            3,
        )
        self.assertEqual(
            self.simulated.matched,
            [[1234567, 11, 1], [1234567, 12, 1], [1234567, 13, 1]],
        )

    def test__process_sp(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated._process_sp(1234571, mock_runner)
        self.assertEqual(self.simulated.matched, [[1234571, 12.2, 2.00]])
        self.assertTrue(self.simulated._bsp_reconciled)
        self.simulated.order.execution_complete.assert_called()

    def test__process_sp_lay(self):
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated.order.side = "LAY"
        self.simulated._process_sp(1234571, mock_runner)
        self.assertEqual(self.simulated.matched, [[1234571, 12.2, 1.96]])
        self.assertEqual(self.simulated.size_cancelled, 0.04)
        self.assertTrue(self.simulated._bsp_reconciled)
        self.simulated.order.execution_complete.assert_called()

    def test__process_sp_lay_liability(self):
        self.simulated.size_matched = 1.90
        mock_runner = mock.Mock()
        mock_runner.sp.actual_sp = 12.20
        self.simulated.order.side = "LAY"
        self.simulated._process_sp(1234571, mock_runner)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated.size_lapsed, 0.10)
        self.assertTrue(self.simulated._bsp_reconciled)
        self.simulated.order.execution_complete.assert_called()

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
        self.simulated.order.execution_complete.assert_called()

    def test__process_sp_limit_on_close_back(self):
        mock_limit_on_close_order = mock.Mock(price=10.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(1234573, mock_runner_book)
        self.assertEqual(self.simulated.matched, [[1234573, 69, 2.00]])
        self.assertTrue(self.simulated._bsp_reconciled)
        self.simulated.order.execution_complete.assert_called()

    def test__process_sp_limit_on_close_back_no_match(self):
        mock_limit_on_close_order = mock.Mock(price=10.0, liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 8
        self.simulated._process_sp(1234574, mock_runner_book)
        self.assertEqual(self.simulated.matched, [])
        self.assertTrue(self.simulated._bsp_reconciled)
        self.simulated.order.execution_complete.assert_called()

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
        self.simulated.order.execution_complete.assert_called()

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
        self.simulated.order.execution_complete.assert_called()

    def test__process_sp_market_on_close_back(self):
        mock_limit_on_close_order = mock.Mock(liability=2.00)
        mock_limit_on_close_order.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.simulated.order.order_type = mock_limit_on_close_order
        mock_runner_book = mock.Mock()
        mock_runner_book.sp.actual_sp = 69
        self.simulated._process_sp(1234577, mock_runner_book)
        self.assertEqual(self.simulated.matched, [[1234577, 69, 2.00]])
        self.assertTrue(self.simulated._bsp_reconciled)
        self.simulated.order.execution_complete.assert_called()

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
        self.simulated.order.execution_complete.assert_called()

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder._calculate_process_traded"
    )
    def test__process_traded_back(self, mock__calculate_process_traded):
        mock__calculate_process_traded.return_value = 5.0
        traded = {12: 120}
        self.simulated._process_traded(1234579, traded)
        mock__calculate_process_traded.assert_called_with(1234579, 120)
        self.assertEqual(traded, {12: 115})

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder._calculate_process_traded"
    )
    def test__process_traded_over_fill(self, mock__calculate_process_traded):
        for side in ("BACK", "LAY"):
            self.simulated.order.side = side
            mock__calculate_process_traded.return_value = 130.0
            traded = {12: 120}
            self.simulated._process_traded(1234579, traded)
            mock__calculate_process_traded.assert_called_with(1234579, 120)
            self.assertEqual(traded, {12: 0})

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder._calculate_process_traded"
    )
    def test__process_traded_back_no(self, mock__calculate_process_traded):
        self.simulated._process_traded(1234580, {11: 120})
        mock__calculate_process_traded.assert_not_called()

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder._calculate_process_traded"
    )
    def test__process_traded_lay(self, mock__calculate_process_traded):
        mock__calculate_process_traded.return_value = 10.0
        self.simulated.order.side = "LAY"
        traded = {12: 120}
        self.simulated._process_traded(1234581, traded)
        mock__calculate_process_traded.assert_called_with(1234581, 120)
        self.assertEqual(traded, {12: 110})

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder._calculate_process_traded"
    )
    def test__process_traded_lay_no(self, mock__calculate_process_traded):
        self.simulated.order.side = "LAY"
        self.simulated._process_traded(1234582, {13: 120})
        mock__calculate_process_traded.assert_not_called()

    def test__calculate_process_traded(self):
        self.assertEqual(self.simulated._calculate_process_traded(1234582, 2.00), 2)
        self.assertEqual(self.simulated._calculate_process_traded(1234583, 2.00), 2)
        self.assertEqual(self.simulated._calculate_process_traded(1234584, 2.00), 0)
        self.assertEqual(
            self.simulated.matched, [[1234582, 12, 1.00], [1234583, 12, 1.00]]
        )
        self.assertEqual(self.simulated._piq, 0)

    def test__calculate_process_traded_piq(self):
        self.simulated._piq = 2.00
        self.assertEqual(self.simulated._calculate_process_traded(1234585, 4.00), 4)
        self.assertEqual(self.simulated.matched, [])
        self.assertEqual(self.simulated._piq, 0)
        self.assertEqual(self.simulated._calculate_process_traded(1234586, 4.00), 4)
        self.assertEqual(self.simulated.matched, [[1234586, 12, 2.00]])
        self.assertEqual(self.simulated._piq, 0)
        self.assertEqual(self.simulated._calculate_process_traded(1234586, 4.00), 0)

    def test__calculate_process_traded_piq_match(self):
        self.simulated._piq = 4.00
        self.assertEqual(self.simulated._calculate_process_traded(1234585, 20.00), 12)
        self.assertEqual(self.simulated.matched, [[1234585, 12, 2.0]])
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

    def test_size_remaining_target(self):
        self.mock_order.order_type.size = None
        self.mock_order.order_type.bet_target_size = 2
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

    def test_profit_dead_heat_back(self):
        self.simulated.order.number_of_dead_heat_winners = 2

        self.simulated.order.runner_status = "WINNER"
        self.simulated._update_matched([1234, 4.0, 10.0])
        self.assertEqual(self.simulated.profit, 10)

        self.simulated.order.runner_status = "LOSER"
        self.assertEqual(self.simulated.profit, -10)

    def test_profit_dead_heat_lay(self):
        self.simulated.order.side = "LAY"
        self.simulated.order.number_of_dead_heat_winners = 2

        self.simulated.order.runner_status = "WINNER"
        self.simulated._update_matched([1234, 5.0, 20.0])
        self.assertEqual(self.simulated.profit, -30)

        self.simulated.order.runner_status = "LOSER"
        self.assertEqual(self.simulated.profit, 20)

    def test_profit_dead_heat_four(self):
        self.simulated.order.number_of_dead_heat_winners = 4
        self.simulated.order.runner_status = "WINNER"
        self.simulated._update_matched([1234, 11.0, 50.0])
        self.assertEqual(self.simulated.profit, 87.50)

    def test_profit_ew_back(self):
        self.simulated.order.market_type = "EACH_WAY"
        self.simulated.order.each_way_divisor = 5
        self.assertEqual(self.simulated.profit, 0)
        self.simulated.order.runner_status = "WINNER"
        self.simulated._update_matched([1234, 10.0, 2.0])
        self.assertEqual(self.simulated.profit, 21.6)
        self.simulated.order.runner_status = "PLACED"
        self.assertEqual(self.simulated.profit, 1.6)
        self.simulated.order.runner_status = "LOSER"
        self.assertEqual(self.simulated.profit, -4.0)

    def test_profit_ew_lay(self):
        self.simulated.order.side = "LAY"
        self.simulated.order.market_type = "EACH_WAY"
        self.simulated.order.each_way_divisor = 5
        self.assertEqual(self.simulated.profit, 0)
        self.simulated.order.runner_status = "WINNER"
        self.simulated._update_matched([1234, 10.0, 2.0])
        self.assertEqual(self.simulated.profit, -21.6)
        self.simulated.order.runner_status = "PLACED"
        self.assertEqual(self.simulated.profit, -1.6)
        self.simulated.order.runner_status = "LOSER"
        self.assertEqual(self.simulated.profit, 4.0)

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.size_remaining",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.take_sp",
        new_callable=mock.PropertyMock,
        return_value=False,
    )
    def test_status(self, mock_take_sp, mock_size_remaining):
        mock_size_remaining.return_value = 1
        self.assertEqual(self.simulated.status, "EXECUTABLE")
        mock_size_remaining.return_value = 0
        self.assertEqual(self.simulated.status, "EXECUTION_COMPLETE")

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.take_sp", return_value=True
    )
    def test_status_sp(self, mock_take_sp):
        self.simulated._bsp_reconciled = False
        self.assertEqual(self.simulated.status, "EXECUTABLE")
        self.simulated._bsp_reconciled = True
        self.assertEqual(self.simulated.status, "EXECUTION_COMPLETE")

    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.size_remaining",
        return_value=1,
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "flumine.simulation.simulatedorder.SimulatedOrder.take_sp",
        return_value=False,
        new_callable=mock.PropertyMock,
    )
    def test_status_limit(self, mock_take_sp, mock_size_remaining):
        self.assertEqual(self.simulated.status, "EXECUTABLE")
        mock_size_remaining.return_value = 0
        self.assertEqual(self.simulated.status, "EXECUTION_COMPLETE")

    def test_info(self):
        self.assertEqual(
            self.simulated.info,
            {
                "profit": 0,
                "piq": 0,
                "matched": [],
            },
        )

    def test_bool(self):
        self.simulated.order.client.paper_trade = False
        self.assertFalse(self.simulated)
        from flumine import config

        config.simulated = True
        self.assertTrue(self.simulated)
        config.simulated = False

    def test_bool_paper_trade(self):
        self.simulated.order.client.paper_trade = False
        self.assertFalse(self.simulated)
        self.simulated.order.client.paper_trade = True
        self.assertTrue(self.simulated)
