import string
import unittest
import datetime
import collections
from unittest import mock

from flumine.order.order import (
    BaseOrder,
    BetfairOrder,
    ExchangeType,
    OrderTypes,
    OrderStatus,
    VALID_BETFAIR_CUSTOMER_ORDER_REF_CHARACTERS,
    LIVE_STATUS,
    COMPLETE_STATUS,
)
from flumine.exceptions import OrderUpdateError


class BaseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        mock_client = mock.Mock(paper_trade=False)
        self.mock_trade = mock.Mock(
            client=mock_client, market_id="1.1", selection_id=123, info={}
        )
        self.mock_order_type = mock.Mock(info={})
        self.order = BaseOrder(
            self.mock_trade, "BACK", self.mock_order_type, 1, context={1: 2}
        )

    def test_init(self):
        self.assertIsNotNone(self.order.id)
        self.assertEqual(self.order.trade, self.mock_trade)
        self.assertEqual(self.order.side, "BACK")
        self.assertEqual(self.order.order_type, self.mock_order_type)
        self.assertEqual(self.order.selection_id, self.mock_trade.selection_id)
        self.assertEqual(self.order.handicap, 1)
        self.assertEqual(
            self.order.lookup,
            (self.order.market_id, self.order.selection_id, self.order.handicap),
        )
        self.assertIsNone(self.order.client)
        self.assertIsNone(self.order.runner_status)
        self.assertIsNone(self.order.market_type)
        self.assertEqual(self.order.each_way_divisor, 1)
        self.assertIsNone(self.order.status)
        self.assertFalse(self.order.complete)
        self.assertEqual(self.order.status_log, [])
        self.assertIsNone(self.order.violation_msg)
        self.assertEqual(self.order.context, {1: 2})
        self.assertEqual(self.order.notes, {})
        self.assertIsNone(self.order.market_notes)
        self.assertIsNone(self.order.bet_id)
        self.assertIsNone(self.order.EXCHANGE)
        self.assertEqual(self.order.update_data, {})
        self.assertIsNone(self.order.publish_time)
        self.assertIsNone(self.order.market_version)
        self.assertIsNone(self.order.async_)
        self.assertIsNotNone(self.order.date_time_created)
        self.assertIsNone(self.order.date_time_execution_complete)
        self.assertFalse(self.order.simulated)
        self.assertFalse(self.order._simulated)
        self.assertEqual(
            LIVE_STATUS,
            [
                OrderStatus.PENDING,
                OrderStatus.CANCELLING,
                OrderStatus.UPDATING,
                OrderStatus.REPLACING,
                OrderStatus.EXECUTABLE,
            ],
        )
        self.assertEqual(
            COMPLETE_STATUS,
            [
                OrderStatus.EXECUTION_COMPLETE,
                OrderStatus.EXPIRED,
                OrderStatus.VIOLATION,
            ],
        )

    @mock.patch("flumine.order.order.BaseOrder._is_complete")
    @mock.patch("flumine.order.order.BaseOrder.info")
    def test__update_status(self, mock_info, mock__is_complete):
        self.mock_trade.complete = True
        self.order._update_status(OrderStatus.EXECUTION_COMPLETE)
        self.assertEqual(self.order.status_log, [OrderStatus.EXECUTION_COMPLETE])
        self.assertEqual(self.order.status, OrderStatus.EXECUTION_COMPLETE)
        self.mock_trade.complete_trade.assert_called()
        mock__is_complete.assert_called()

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_placing(self, mock__update_status):
        self.order.placing()
        mock__update_status.assert_called_with(OrderStatus.PENDING)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_executable(self, mock__update_status):
        self.order.update_data = {123: 456}
        self.order.executable()
        mock__update_status.assert_called_with(OrderStatus.EXECUTABLE)
        self.assertEqual(self.order.update_data, {})

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_execution_complete(self, mock__update_status):
        self.order.update_data = {123: 456}
        self.order.execution_complete()
        mock__update_status.assert_called_with(OrderStatus.EXECUTION_COMPLETE)
        self.assertIsNotNone(self.order.date_time_execution_complete)
        self.assertEqual(self.order.update_data, {})

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_cancelling(self, mock__update_status):
        self.order.cancelling()
        mock__update_status.assert_called_with(OrderStatus.CANCELLING)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_updating(self, mock__update_status):
        self.order.updating()
        mock__update_status.assert_called_with(OrderStatus.UPDATING)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_replacing(self, mock__update_status):
        self.order.replacing()
        mock__update_status.assert_called_with(OrderStatus.REPLACING)

    @mock.patch("flumine.order.order.BaseOrder._update_status")
    def test_violation(self, mock__update_status):
        self.order.update_data = {123: 456}
        self.order.violation("the murder capital")
        mock__update_status.assert_called_with(OrderStatus.VIOLATION)
        self.assertEqual(self.order.update_data, {})
        self.assertEqual(self.order.violation_msg, "the murder capital")

    def test_place(self):
        with self.assertRaises(NotImplementedError):
            self.order.place(123, 456, False)

    def test_cancel(self):
        with self.assertRaises(NotImplementedError):
            self.order.cancel()

    def test_update(self):
        with self.assertRaises(NotImplementedError):
            self.order.update("PERSIST")

    def test_replace(self):
        with self.assertRaises(NotImplementedError):
            self.order.replace(20.0)

    def test_create_place_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order.create_place_instruction()

    def test_create_cancel_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order.create_cancel_instruction()

    def test_create_update_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order.create_update_instruction()

    def test_create_replace_instruction(self):
        with self.assertRaises(NotImplementedError):
            self.order.create_replace_instruction()

    def test_update_current_order(self):
        mock_current_order = mock.Mock()
        self.order.update_current_order(mock_current_order)
        self.assertEqual(self.order.responses.current_order, mock_current_order)

    def test_update_client(self):
        self.order._simulated = False
        mock_client = mock.Mock(paper_trade=True)
        self.order.update_client(mock_client)
        self.assertEqual(self.order.client, mock_client)
        self.assertTrue(self.order._simulated)

    def test_current_order(self):
        self.assertIsNone(self.order.current_order)
        mock_responses = mock.Mock()
        mock_responses.current_order = None
        self.order.responses = mock_responses
        self.assertEqual(self.order.current_order, mock_responses.place_response)
        mock_responses.current_order = 1
        self.assertEqual(self.order.current_order, 1)

    @mock.patch("flumine.simulation.simulatedorder.config")
    def test_current_order_simulated(self, mock_config):
        mock_config.simulated = True
        order = BaseOrder(mock.Mock(), "", mock.Mock())
        self.assertTrue(order.simulated)
        self.assertTrue(order._simulated)

    def test__is_complete(self):
        self.order.status = None
        self.assertFalse(self.order._is_complete())
        for s in [
            OrderStatus.PENDING,
            OrderStatus.CANCELLING,
            OrderStatus.UPDATING,
            OrderStatus.REPLACING,
            OrderStatus.EXECUTABLE,
        ]:
            self.order.status = s
            self.assertFalse(self.order._is_complete())
        for s in [
            OrderStatus.EXECUTION_COMPLETE,
            OrderStatus.EXPIRED,
            OrderStatus.VIOLATION,
        ]:
            self.order.status = s
            self.assertTrue(self.order._is_complete())

    def test_average_price_matched(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.average_price_matched

    def test_size_matched(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_matched

    def test_size_remaining(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_remaining

    def test_size_cancelled(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_cancelled

    def test_size_lapsed(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_lapsed

    def test_size_voided(self):
        with self.assertRaises(NotImplementedError):
            assert self.order.size_voided

    def test_elapsed_seconds(self):
        self.assertIsNone(self.order.elapsed_seconds)
        mock_responses = mock.Mock()
        mock_responses.date_time_placed = datetime.datetime.utcnow()
        self.order.responses = mock_responses
        self.assertGreaterEqual(self.order.elapsed_seconds, 0)

    def elapsed_seconds_created(self):
        self.assertGreaterEqual(self.order.elapsed_seconds_created, 0)

    def test_elapsed_seconds_executable(self):
        self.assertIsNone(self.order.elapsed_seconds_executable)
        mock_responses = mock.Mock()
        mock_responses.date_time_placed = datetime.datetime.utcnow()
        self.order.responses = mock_responses
        self.order.date_time_execution_complete = datetime.datetime.utcnow()
        self.assertGreaterEqual(self.order.elapsed_seconds_executable, 0)

    def test_profit(self):
        self.order._simulated = True
        mock_simulated = mock.Mock(profit=1)
        self.order.simulated = mock_simulated
        self.assertEqual(self.order.profit, 1)

    def test_profit_cleared(self):
        self.order._simulated = False
        self.assertEqual(self.order.profit, 0)
        mock_cleared = mock.Mock(profit=1)
        self.order.cleared_order = mock_cleared
        self.assertEqual(self.order.profit, 1)

    def test_market_id(self):
        self.assertEqual(self.order.market_id, self.mock_trade.market_id)

    def test_lookup(self):
        self.assertEqual(
            self.order.lookup,
            (self.mock_trade.market_id, self.mock_trade.selection_id, 1),
        )

    def test_repr(self):
        self.assertEqual(repr(self.order), "Order None: None")

    def test_set_and_get_sep(self):
        self.order.sep = "a"
        self.assertEqual("a", self.order.sep)

    def test_customer_order_ref(self):
        self.order.trade.strategy.name_hash = "my_name_hash"
        self.order.id = 1234
        self.assertEqual("my_name_hash-1234", self.order.customer_order_ref)

        self.order.sep = "I"
        self.assertEqual("my_name_hashI1234", self.order.customer_order_ref)

        self.order.sep = "O"
        self.assertEqual("my_name_hashO1234", self.order.customer_order_ref)

    def test_notes_str(self):
        self.order.notes = collections.OrderedDict({"1": 1, 2: "2", 3: 3, 4: "four"})
        self.assertEqual(self.order.notes_str, "1,2,3,four")
        self.order.notes = collections.OrderedDict()
        self.assertEqual(self.order.notes_str, "")


class BetfairOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        mock_client = mock.Mock(paper_trade=False)
        self.mock_trade = mock.Mock(
            client=mock_client, market_id="1.1", selection_id=123, info={}
        )
        self.mock_status = mock.Mock()
        self.mock_order_type = mock.Mock(info={}, size=2.0, liability=2.0)
        self.order = BetfairOrder(self.mock_trade, "BACK", self.mock_order_type)

    def test_init(self):
        self.assertEqual(self.order.EXCHANGE, ExchangeType.BETFAIR)

    @mock.patch("flumine.order.order.BetfairOrder.placing")
    def test_place(self, mock_placing):
        self.order.place(123, 456, False)
        self.assertFalse(self.order._simulated)
        self.assertEqual(self.order.publish_time, 123)
        self.assertEqual(self.order.market_version, 456)
        self.assertFalse(self.order.async_)
        mock_placing.assert_called_with()

    @mock.patch(
        "flumine.order.order.BetfairOrder.size_remaining",
        new_callable=mock.PropertyMock,
    )
    @mock.patch("flumine.order.order.BetfairOrder.cancelling")
    def test_cancel(self, mock_cancelling, mock_size_remaining):
        mock_size_remaining.return_value = 20
        self.order.bet_id = 123
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(12)

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.order.cancel(0.01)
        self.assertEqual(self.order.update_data, {"size_reduction": 0.01})
        mock_cancelling.assert_called_with()
        self.order.cancel()
        self.assertEqual(self.order.update_data, {"size_reduction": None})

    def test_cancel_bet_id(self):
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(12)

    @mock.patch(
        "flumine.order.order.BetfairOrder.size_remaining",
        new_callable=mock.PropertyMock,
    )
    @mock.patch("flumine.order.order.BetfairOrder.cancelling")
    def test_cancel_error_size(self, mock_cancelling, mock_size_remaining):
        mock_size_remaining.return_value = 20
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(12)

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(21)

    @mock.patch(
        "flumine.order.order.BetfairOrder.size_remaining",
        new_callable=mock.PropertyMock,
    )
    def test_cancel_error(self, mock_size_remaining):
        mock_size_remaining.return_value = 20
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.order.status = OrderStatus.PENDING
        with self.assertRaises(OrderUpdateError):
            self.order.cancel(12)

    @mock.patch("flumine.order.order.BetfairOrder.updating")
    def test_update(self, mock_updating):
        self.order.bet_id = 123
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.persistence_type = "LAPSE"
        self.order.update("PERSIST")
        self.assertEqual(self.mock_order_type.persistence_type, "PERSIST")
        mock_updating.assert_called_with()

        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

    def test_update_bet_id(self):
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

    def test_update_error(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.persistence_type = "LAPSE"
        self.order.status = OrderStatus.PENDING
        with self.assertRaises(OrderUpdateError):
            self.order.update("PERSIST")

    @mock.patch("flumine.order.order.BetfairOrder.replacing")
    def test_replace(self, mock_replacing):
        self.order.bet_id = 123
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.replace(1.01)

        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.price = 2.02
        self.order.replace(1.01)
        self.assertEqual(self.order.update_data, {"new_price": 1.01})
        mock_replacing.assert_called_with()

        with self.assertRaises(OrderUpdateError):
            self.order.replace(2.02)

    def test_replace_bet_id(self):
        self.order.status = OrderStatus.EXECUTABLE
        with self.assertRaises(OrderUpdateError):
            self.order.replace(1.01)

    def test_replace_error(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.order.status = OrderStatus.PENDING
        with self.assertRaises(OrderUpdateError):
            self.order.replace(1.52)

    def test_create_place_instruction(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.assertEqual(
            self.order.create_place_instruction(),
            {
                "customerOrderRef": self.order.customer_order_ref,
                "handicap": 0,
                "limitOrder": self.mock_order_type.place_instruction(),
                "orderType": "LIMIT",
                "selectionId": self.mock_trade.selection_id,
                "side": "BACK",
            },
        )
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.assertEqual(
            self.order.create_place_instruction(),
            {
                "customerOrderRef": self.order.customer_order_ref,
                "handicap": 0,
                "limitOnCloseOrder": self.mock_order_type.place_instruction(),
                "orderType": "LIMIT_ON_CLOSE",
                "selectionId": self.mock_trade.selection_id,
                "side": "BACK",
            },
        )
        self.mock_order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.assertEqual(
            self.order.create_place_instruction(),
            {
                "customerOrderRef": self.order.customer_order_ref,
                "handicap": 0,
                "marketOnCloseOrder": self.mock_order_type.place_instruction(),
                "orderType": "MARKET_ON_CLOSE",
                "selectionId": self.mock_trade.selection_id,
                "side": "BACK",
            },
        )

    def test_create_cancel_instruction(self):
        self.order.update_data = {"size_reduction": 0.02}
        self.assertEqual(
            self.order.create_cancel_instruction(), {"sizeReduction": 0.02}
        )

    def test_create_update_instruction(self):
        self.mock_order_type.persistence_type = "PERSIST"
        self.assertEqual(
            self.order.create_update_instruction(), {"newPersistenceType": "PERSIST"}
        )

    def test_create_replace_instruction(self):
        self.order.update_data = {"new_price": 2.02}
        self.assertEqual(self.order.create_replace_instruction(), {"newPrice": 2.02})

    def test_average_price_matched(self):
        self.assertEqual(self.order.average_price_matched, 0)
        mock_current_order = mock.Mock(average_price_matched=12.3)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(
            self.order.average_price_matched, mock_current_order.average_price_matched
        )

    def test_size_matched(self):
        self.assertEqual(self.order.size_matched, 0)
        mock_current_order = mock.Mock(size_matched=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_matched, mock_current_order.size_matched)

    def test_size_remaining(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.size = 0
        self.mock_order_type.bet_target_size = 0
        self.assertEqual(self.order.size_remaining, 0)
        self.mock_order_type.size = 10
        mock_current_order = mock.Mock(size_remaining=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_remaining, mock_current_order.size_remaining)

    def test_size_remaining_missing(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.mock_order_type.size = 2.51
        self.assertEqual(self.order.size_remaining, 2.51)

    @mock.patch(
        "flumine.order.order.BetfairOrder.size_matched",
        new_callable=mock.PropertyMock,
    )
    def test_size_remaining_missing_partial_match(self, mock_size_matched):
        self.mock_order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_size_matched.return_value = 2
        self.mock_order_type.size = 10
        self.assertEqual(self.order.size_remaining, 8)

    def test_size_remaining_market_on_close(self):
        self.mock_order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.mock_order_type.size = ValueError
        self.order.responses.current_order = None
        self.assertEqual(self.order.size_remaining, self.mock_order_type.liability)

    def test_size_cancelled(self):
        self.assertEqual(self.order.size_cancelled, 0)
        mock_current_order = mock.Mock(size_cancelled=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_cancelled, mock_current_order.size_cancelled)

    def test_size_lapsed(self):
        self.assertEqual(self.order.size_lapsed, 0)
        mock_current_order = mock.Mock(size_lapsed=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_lapsed, mock_current_order.size_lapsed)

    def test_size_voided(self):
        self.assertEqual(self.order.size_voided, 0)
        mock_current_order = mock.Mock(size_voided=10)
        self.order.responses.current_order = mock_current_order
        self.assertEqual(self.order.size_voided, mock_current_order.size_voided)

    def test_info(self):
        self.order.status_log = [OrderStatus.PENDING, OrderStatus.EXECUTION_COMPLETE]
        self.assertEqual(
            self.order.info,
            {
                "bet_id": None,
                "handicap": self.order.handicap,
                "id": self.order.id,
                "date_time_created": str(self.order.date_time_created),
                "market_id": self.mock_trade.market_id,
                "selection_id": self.mock_trade.selection_id,
                "publish_time": None,
                "market_version": None,
                "async": None,
                "status": None,
                "status_log": "Pending, Execution complete",
                "trade": self.mock_trade.info,
                "order_type": self.mock_order_type.info,
                "info": {
                    "side": self.order.side,
                    "size_matched": self.order.size_matched,
                    "size_remaining": self.order.size_remaining,
                    "size_cancelled": self.order.size_cancelled,
                    "size_lapsed": self.order.size_lapsed,
                    "size_voided": self.order.size_voided,
                    "average_price_matched": self.order.average_price_matched,
                },
                "customer_order_ref": self.order.customer_order_ref,
                "simulated": {
                    "profit": 0.0,
                    "piq": 0.0,
                    "matched": [],
                },
                "violation_msg": self.order.violation_msg,
                "responses": {
                    "date_time_placed": None,
                    "elapsed_seconds_executable": None,
                },
                "runner_status": self.order.runner_status,
                "market_notes": None,
                "notes": "",
                "client": None,
            },
        )

    def test_json(self):
        self.assertTrue(isinstance(self.order.json(), str))

    def test_set_invalid_sep(self):
        with self.assertRaises(ValueError):
            self.order.sep = "@"


class IsValidCustomerOrderRefTestCase(unittest.TestCase):
    def test_letters_True(self):
        # ascii_letters contains a-z and A-Z
        for c in string.ascii_letters:
            self.assertTrue(BetfairOrder.is_valid_customer_order_ref_character(c))

    def test_2letters_False(self):
        self.assertFalse(BetfairOrder.is_valid_customer_order_ref_character("aB"))
        self.assertFalse(BetfairOrder.is_valid_customer_order_ref_character("CD"))

    def test_digits_True(self):
        # string.digits contains digits 0-9
        for c in string.digits:
            self.assertTrue(BetfairOrder.is_valid_customer_order_ref_character(c))

    def test_special_characters_True(self):
        for c in VALID_BETFAIR_CUSTOMER_ORDER_REF_CHARACTERS:
            self.assertTrue(BetfairOrder.is_valid_customer_order_ref_character((c)))

    def test_special_characters_False(self):
        for c in list('!"£$%'):
            self.assertFalse(BetfairOrder.is_valid_customer_order_ref_character((c)))
