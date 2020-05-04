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

    def test_wap(self):
        matched = [(1.5, 100), (1.6, 100)]
        assert self.simulated._wap(matched) == (200, 1.55)

    def test_wap_nothing(self):
        matched = []
        assert self.simulated._wap(matched) == (0, 0)

    def test_wap_error(self):
        matched = [(1.5, 0)]
        assert self.simulated._wap(matched) == (0, 0)

    def test_average_price_matched(self):
        self.assertEqual(self.simulated.average_price_matched, 0)
        self.simulated.matched = [(1, 2)]
        self.assertEqual(self.simulated.average_price_matched, 1)

    def test_size_matched(self):
        self.assertEqual(self.simulated.size_matched, 0)
        self.simulated.matched = [(1, 2)]
        self.assertEqual(self.simulated.size_matched, 2)

    def test_side(self):
        self.assertEqual(self.simulated.side, self.mock_order.side)
