import unittest
from unittest import mock

from betdaq.enums import OrderKillType, WithdrawRepriceOption

from flumine.order.ordertype import (
    ExchangeType,
    OrderTypes,
    BaseOrderType,
    LimitOrder,
    LimitOnCloseOrder,
    MarketOnCloseOrder,
    BetdaqLimitOrder,
)


class BaseOrderTypeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order_type = BaseOrderType()

    def test_init(self):
        self.assertIsNone(self.order_type.EXCHANGE)
        self.assertIsNone(self.order_type.ORDER_TYPE)

    def test_place_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order_type.place_instruction()

    def test_info(self):
        with self.assertRaises(NotImplementedError):
            assert self.order_type.info


class LimitOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_line_range_info = mock.Mock()
        self.order_type = LimitOrder(
            1.01,
            2,
            "PERSIST",
            "YES",
            34.5,
            "NO",
            2,
            "FINEST",
            self.mock_line_range_info,
        )

    def test_init(self):
        self.assertEqual(self.order_type.EXCHANGE, ExchangeType.BETFAIR)
        self.assertEqual(self.order_type.ORDER_TYPE, OrderTypes.LIMIT)
        self.assertEqual(self.order_type.price, 1.01)
        self.assertEqual(self.order_type.size, 2)
        self.assertEqual(self.order_type.persistence_type, "PERSIST")
        self.assertEqual(self.order_type.time_in_force, "YES")
        self.assertEqual(self.order_type.min_fill_size, 34.5)
        self.assertEqual(self.order_type.bet_target_type, "NO")
        self.assertEqual(self.order_type.bet_target_size, 2)
        self.assertEqual(self.order_type.price_ladder_definition, "FINEST")
        self.assertEqual(self.order_type.line_range_info, self.mock_line_range_info)

    def test_place_instruction(self):
        self.assertEqual(
            self.order_type.place_instruction(),
            {
                "betTargetSize": 2,
                "betTargetType": "NO",
                "minFillSize": 34.5,
                "persistenceType": "PERSIST",
                "price": 1.01,
                "size": 2,
                "timeInForce": "YES",
            },
        )

    def test_info(self):
        self.assertEqual(
            self.order_type.info,
            {
                "bet_target_size": 2,
                "bet_target_type": "NO",
                "min_fill_size": 34.5,
                "order_type": "Limit",
                "persistence_type": "PERSIST",
                "price": 1.01,
                "size": 2,
                "time_in_force": "YES",
                "price_ladder_definition": "FINEST",
            },
        )


class LimitOnCloseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order_type = LimitOnCloseOrder(64, 1.01)

    def test_init(self):
        self.assertEqual(self.order_type.EXCHANGE, ExchangeType.BETFAIR)
        self.assertEqual(self.order_type.ORDER_TYPE, OrderTypes.LIMIT_ON_CLOSE)
        self.assertEqual(self.order_type.liability, 64)
        self.assertEqual(self.order_type.price, 1.01)
        self.assertEqual(self.order_type.price_ladder_definition, "CLASSIC")

    def test_place_instruction(self):
        self.assertEqual(
            self.order_type.place_instruction(), {"price": 1.01, "liability": 64}
        )

    def test_info(self):
        self.assertEqual(
            self.order_type.info,
            {
                "liability": 64,
                "order_type": "Limit on close",
                "price": 1.01,
                "price_ladder_definition": "CLASSIC",
            },
        )


class MarketOnCloseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order_type = MarketOnCloseOrder(128)

    def test_init(self):
        self.assertEqual(self.order_type.EXCHANGE, ExchangeType.BETFAIR)
        self.assertEqual(self.order_type.ORDER_TYPE, OrderTypes.MARKET_ON_CLOSE)
        self.assertEqual(self.order_type.liability, 128)

    def test_place_instruction(self):
        self.assertEqual(self.order_type.place_instruction(), {"liability": 128})

    def test_info(self):
        self.assertEqual(
            self.order_type.info, {"liability": 128, "order_type": "Market on close"}
        )


class BetdaqLimitOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_line_range_info = mock.Mock()
        self.order_type = BetdaqLimitOrder(
            1.01,
            2,
            123,
            12,
            34,
        )

    def test_init(self):
        self.assertEqual(self.order_type.EXCHANGE, ExchangeType.BETDAQ)
        self.assertEqual(self.order_type.ORDER_TYPE, OrderTypes.LIMIT)
        self.assertEqual(self.order_type.price, 1.01)
        self.assertEqual(self.order_type.size, 2)
        self.assertEqual(self.order_type.betdaq_runner_id, 123)
        self.assertEqual(self.order_type.runner_reset_count, 12)
        self.assertEqual(self.order_type.withdrawal_sequence_number, 34)
        self.assertEqual(
            self.order_type.kill_type, OrderKillType.FillOrKillDontCancel.value
        )
        self.assertEqual(self.order_type.fill_or_kill_threshold, 0.0)
        self.assertTrue(self.order_type.cancel_on_in_running)
        self.assertTrue(self.order_type.cancel_if_selection_reset)
        self.assertEqual(
            self.order_type.withdrawal_reprice_option,
            WithdrawRepriceOption.Cancel.value,
        )

    def test_place_instruction(self):
        self.assertEqual(
            self.order_type.place_instruction(1, "test"),
            {
                "CancelIfSelectionReset": True,
                "CancelOnInRunning": True,
                "ExpectedSelectionResetCount": 12,
                "ExpectedWithdrawalSequenceNumber": 34,
                "FillOrKillThreshold": 0.0,
                "KillType": OrderKillType.FillOrKillDontCancel.value,
                "Polarity": 1,
                "Price": 1.01,
                "PunterReferenceNumber": "test",
                "SelectionId": 123,
                "Stake": 2,
                "WithdrawalRepriceOption": WithdrawRepriceOption.Cancel.value,
            },
        )

    def test_info(self):
        self.assertEqual(
            self.order_type.info,
            {
                "betdaq_runner_id": 123,
                "cancel_if_selection_reset": True,
                "cancel_on_in_running": True,
                "fill_or_kill_threshold": 0.0,
                "kill_type": OrderKillType.FillOrKillDontCancel.value,
                "order_type": OrderTypes.LIMIT,
                "price": 1.01,
                "runner_reset_count": 12,
                "size": 2,
                "withdrawal_reprice_option": WithdrawRepriceOption.Cancel.value,
                "withdrawal_sequence_number": 34,
            },
        )
