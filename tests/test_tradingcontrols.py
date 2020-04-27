import unittest
from unittest import mock

from flumine.controls.tradingcontrols import OrderValidation, OrderTypes, ExchangeType


class TestOrderValidation(unittest.TestCase):
    def setUp(self):
        self.mock_flumine = mock.Mock()
        self.mock_client = mock.Mock()
        self.mock_client.min_bet_size = 2
        self.mock_client.min_bsp_liability = 10
        self.trading_control = OrderValidation(self.mock_flumine)

    def test_init(self):
        assert self.trading_control.NAME == "ORDER_VALIDATION"

    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_order"
    )
    def test_validate_betfair(self, mock_validate_betfair_order):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        order.EXCHANGE = ExchangeType.BETFAIR
        order.order_type.size = 12
        order_package = [order]

        self.trading_control._validate(order_package)
        mock_validate_betfair_order.assert_called_with(order)

    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_size"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_price"
    )
    def test__validate_betfair_order_limit(
        self, mock__validate_betfair_price, mock__validate_betfair_size
    ):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.trading_control._validate_betfair_order(order)
        mock__validate_betfair_price.assert_called_with(order)
        mock__validate_betfair_size.assert_called_with(order)

    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_price"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_min_size"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_liability"
    )
    def test__validate_betfair_order_limit_on_close(
        self,
        mock__validate_betfair_liability,
        mock__validate_betfair_min_size,
        mock__validate_betfair_price,
    ):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.trading_control._validate_betfair_order(order)
        mock__validate_betfair_liability.assert_called_with(order)
        mock__validate_betfair_min_size.assert_called_with(order)
        mock__validate_betfair_price.assert_called_with(order)

    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_min_size"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_liability"
    )
    def test__validate_betfair_order_market_on_close(
        self, mock__validate_betfair_liability, mock__validate_betfair_min_size
    ):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.trading_control._validate_betfair_order(order)
        mock__validate_betfair_liability.assert_called_with(order)
        mock__validate_betfair_min_size.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_order_unknown(self, mock_on_error):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = "RUSH"
        self.trading_control._validate_betfair_order(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_size(self, mock_on_error):
        order = mock.Mock()
        order.order_type.size = 2
        self.trading_control._validate_betfair_size(order)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_size_on_error(self, mock_on_error):
        order = mock.Mock()
        order.order_type.size = None
        self.trading_control._validate_betfair_size(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_size_on_error_two(self, mock_on_error):
        order = mock.Mock()
        order.order_type.size = -1
        self.trading_control._validate_betfair_size(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_size_on_error_three(self, mock_on_error):
        order = mock.Mock()
        order.order_type.size = 1.999
        self.trading_control._validate_betfair_size(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_price(self, mock_on_error):
        order = mock.Mock()
        order.order_type.price = 2
        self.trading_control._validate_betfair_price(order)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_price_on_error(self, mock_on_error):
        order = mock.Mock()
        order.order_type.price = None
        self.trading_control._validate_betfair_price(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_price_on_error_two(self, mock_on_error):
        order = mock.Mock()
        order.order_type.price = -1
        self.trading_control._validate_betfair_price(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_liability(self, mock_on_error):
        order = mock.Mock()
        order.order_type.liability = 2
        self.trading_control._validate_betfair_liability(order)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_liability_on_error(self, mock_on_error):
        order = mock.Mock()
        order.order_type.liability = None
        self.trading_control._validate_betfair_liability(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_liability_on_error_two(self, mock_on_error):
        order = mock.Mock()
        order.order_type.liability = -1
        self.trading_control._validate_betfair_liability(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size(self, mock_on_error):
        order = mock.Mock()
        order.client = self.mock_client
        order.side = "BACK"
        order.order_type.liability = 2
        self.trading_control._validate_betfair_min_size(order)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_two(self, mock_on_error):
        order = mock.Mock()
        order.client = self.mock_client
        order.side = "LAY"
        order.order_type.liability = 10
        self.trading_control._validate_betfair_min_size(order)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_on_error(self, mock_on_error):
        order = mock.Mock()
        order.client = self.mock_client
        order.side = "BACK"
        order.order_type.liability = 1.99
        self.trading_control._validate_betfair_min_size(order)
        mock_on_error.assert_called_with(order)

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_on_error_two(self, mock_on_error):
        order = mock.Mock()
        order.client = self.mock_client
        order.side = "LAY"
        order.order_type.liability = 9.99
        self.trading_control._validate_betfair_min_size(order)
        mock_on_error.assert_called_with(order)
