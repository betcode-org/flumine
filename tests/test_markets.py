import unittest
import datetime
from unittest import mock

from flumine.markets.markets import Markets
from flumine.markets.market import Market
from flumine import config


class MarketsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.markets = Markets()

    def test_init(self):
        self.assertEqual(self.markets._markets, {})
        self.assertEqual(self.markets.events, {})

    def test_add_market(self):
        mock_market = mock.Mock(event_id="1234")
        self.markets.add_market("1.1", mock_market)
        self.assertEqual(self.markets._markets, {"1.1": mock_market})
        self.assertEqual(self.markets.events, {"1234": [mock_market]})

    def test_add_market_no_event_id(self):
        mock_market = mock.Mock(event_id=None)
        self.markets.add_market("1.1", mock_market)
        self.assertEqual(self.markets._markets, {"1.1": mock_market})
        self.assertEqual(self.markets.events, {})

    def test_add_market_reopen(self):
        mock_market = mock.Mock()
        self.markets._markets = {"1.1": mock_market}
        self.markets.add_market("1.1", mock_market)

        self.assertEqual(self.markets._markets, {"1.1": mock_market})
        mock_market.open_market.assert_called_with()

    def test_close_market(self):
        mock_market = mock.Mock()
        self.markets._markets = {"1.1": mock_market}
        self.markets.close_market("1.1")
        mock_market.close_market.assert_called_with()

    def test_remove_market(self):
        mock_market = mock.Mock(event_id=1234)
        self.markets._markets = {"1.1": mock_market}
        self.markets.events = {1234: [mock_market]}
        self.markets.remove_market("1.1")
        self.assertEqual(self.markets._markets, {})
        self.assertEqual(self.markets.events, {1234: []})

    def test_remove_market_no_event(self):
        mock_market = mock.Mock(event_id=1234)
        self.markets._markets = {"1.1": mock_market}
        self.markets.remove_market("1.1")
        self.assertEqual(self.markets._markets, {})
        self.assertEqual(self.markets.events, {})

    def test_remove_market_err(self):
        mock_market = mock.Mock(event_id=1234)
        mock_market_two = mock.Mock(event_id=1234)
        self.markets._markets = {"1.1": mock_market, "2.2": mock_market_two}
        self.markets.events = {1234: [mock_market]}
        self.markets.remove_market("2.2")
        self.assertEqual(self.markets._markets, {"1.1": mock_market})
        self.assertEqual(self.markets.events, {1234: [mock_market]})

    def test_get_order(self):
        mock_market = mock.Mock()
        mock_market.closed = False
        mock_market.blotter = {"test": 12}
        self.markets._markets = {"1.1": mock_market}

        self.assertEqual(self.markets.get_order("1.1", "test"), 12)
        self.assertIsNone(self.markets.get_order("1.2", "test"))

    def test_get_order_from_bet_id(self):
        mock_blotter = mock.Mock()
        mock_market = mock.Mock(closed=False, blotter=mock_blotter)
        self.markets._markets = {"1.1": mock_market}
        self.markets.get_order_from_bet_id("1.1", "321")
        mock_blotter.get_order_bet_id.assert_called_with("321")

    def test_markets(self):
        self.assertEqual(self.markets.markets, {})
        mock_market = mock.Mock()
        mock_market_two = mock.Mock()
        self.markets._markets = {"1.1": mock_market, "2.1": mock_market_two}
        self.assertEqual(
            self.markets.markets, {"1.1": mock_market, "2.1": mock_market_two}
        )

    def test_open_market_ids(self):
        self.assertEqual(self.markets.open_market_ids, [])
        mock_market = mock.Mock(status="OPEN")
        mock_market_two = mock.Mock(status="CLOSED")
        self.markets._markets = {"1.1": mock_market, "2.1": mock_market_two}
        self.assertEqual(self.markets.open_market_ids, [mock_market.market_id])

    def test_live_orders(self):
        self.assertFalse(self.markets.live_orders)
        mock_market = mock.Mock()
        mock_market.closed = False
        mock_market.blotter.has_live_orders = True
        self.markets._markets = {"1.234": mock_market}
        self.assertTrue(self.markets.live_orders)
        mock_market.blotter.has_live_orders = False
        self.assertFalse(self.markets.live_orders)

    def test_iter(self):
        self.assertEqual(len([i for i in self.markets]), 0)

    def test_len(self):
        self.assertEqual(len(self.markets), 0)


class MarketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.mock_market_book = mock.Mock()
        self.mock_market_catalogue = mock.Mock()
        self.market = Market(
            self.mock_flumine,
            "1.234",
            self.mock_market_book,
            self.mock_market_catalogue,
        )

    def test_init(self):
        self.assertEqual(self.market.flumine, self.mock_flumine)
        self.assertEqual(self.market.market_id, "1.234")
        self.assertFalse(self.market.closed)
        self.assertIsNotNone(self.market.date_time_created)
        self.assertIsNone(self.market.date_time_closed)
        self.assertEqual(self.market.market_book, self.mock_market_book)
        self.assertEqual(self.market.market_catalogue, self.mock_market_catalogue)
        self.assertTrue(self.market.update_market_catalogue)
        self.assertEqual(self.market.orders_cleared, [])
        self.assertEqual(self.market.market_cleared, [])
        self.assertEqual(self.market.context, {"simulated": {}})
        self.assertIsNotNone(self.market.blotter)
        self.assertEqual(self.market._transaction_id, 0)

    def test_call(self):
        mock_market_book = mock.Mock()
        self.market(mock_market_book)
        self.assertEqual(self.market.market_book, mock_market_book)
        self.assertTrue(self.market.update_market_catalogue)

    def test_open_market(self):
        self.market.closed = True
        self.market.orders_cleared = [1, 2]
        self.market.market_cleared = [1]
        self.market.open_market()
        self.assertFalse(self.market.closed)
        self.assertEqual(self.market.orders_cleared, [])
        self.assertEqual(self.market.market_cleared, [])

    def test_close_market(self):
        self.market.close_market()
        self.assertTrue(self.market.closed)
        self.assertIsNotNone(self.market.date_time_closed)

    @mock.patch("flumine.markets.market.Transaction")
    def test_transaction(self, mock_transaction):
        transaction = self.market.transaction()
        mock_transaction.assert_called_with(
            self.market,
            id_=self.market._transaction_id,
            async_place_orders=False,
            client=self.market.flumine.clients.get_default(),
        )
        self.assertEqual(transaction, mock_transaction())

    @mock.patch("flumine.markets.market.Transaction")
    def test_transaction_async(self, mock_transaction):
        config.async_place_orders = True
        transaction = self.market.transaction()
        mock_transaction.assert_called_with(
            self.market,
            id_=self.market._transaction_id,
            async_place_orders=True,
            client=self.market.flumine.clients.get_default(),
        )
        self.assertEqual(transaction, mock_transaction())

    @mock.patch("flumine.markets.market.Market.transaction")
    def test_place_order(self, mock_transaction):
        mock_transaction.return_value.__enter__.return_value = mock_transaction
        mock_order = mock.Mock()
        self.assertTrue(
            self.market.place_order(mock_order, 2, False, force=True, client=1)
        )
        mock_transaction.assert_called_with(client=1)
        mock_transaction.place_order.assert_called_with(mock_order, 2, False, True)

    @mock.patch("flumine.markets.market.Market.transaction")
    def test_cancel_order(self, mock_transaction):
        mock_transaction.return_value.__enter__.return_value = mock_transaction
        mock_order = mock.Mock()
        self.assertTrue(self.market.cancel_order(mock_order, 2.02, force=True))
        mock_transaction.assert_called_with(client=mock_order.client)
        mock_transaction.cancel_order.assert_called_with(mock_order, 2.02, True)

    @mock.patch("flumine.markets.market.Market.transaction")
    def test_update_order(self, mock_transaction):
        mock_transaction.return_value.__enter__.return_value = mock_transaction
        mock_order = mock.Mock()
        self.assertTrue(self.market.update_order(mock_order, "test", force=True))
        mock_transaction.assert_called_with(client=mock_order.client)
        mock_transaction.update_order.assert_called_with(mock_order, "test", True)

    @mock.patch("flumine.markets.market.Market.transaction")
    def test_replace_order(self, mock_transaction):
        mock_transaction.return_value.__enter__.return_value = mock_transaction
        mock_order = mock.Mock()
        self.assertTrue(self.market.replace_order(mock_order, 2, False, force=True))
        mock_transaction.assert_called_with(client=mock_order.client)
        mock_transaction.replace_order.assert_called_with(mock_order, 2, False, True)

    def test_event(self):
        self.market.market_catalogue.event.id = 12
        self.market.market_book.market_definition.market_time = 12

        self.market.flumine.markets = []
        self.assertEqual(self.market.event, {})

        m_one = mock.Mock(market_type=1, event_id=12, market_start_datetime=12)
        m_two = mock.Mock(market_type=2, event_id=12, market_start_datetime=12)
        m_three = mock.Mock(market_type=3, event_id=123, market_start_datetime=12)
        m_four = mock.Mock(market_type=1, event_id=12, market_start_datetime=12)
        m_five = mock.Mock(market_type=2, event_id=12, market_start_datetime=13)
        self.market.flumine.markets = [m_one, m_two, m_three, m_four, m_five]
        self.assertEqual(self.market.event, {1: [m_one, m_four], 2: [m_two]})

    def test_event_type_id_mc(self):
        mock_market_catalogue = mock.Mock()
        self.market.market_catalogue = mock_market_catalogue
        self.assertEqual(self.market.event_type_id, mock_market_catalogue.event_type.id)

    def test_event_type_id_mb(self):
        self.market.market_catalogue = None
        mock_market_book = mock.Mock()
        self.market.market_book = mock_market_book
        self.assertEqual(
            self.market.event_type_id, mock_market_book.market_definition.event_type_id
        )

    def test_event_id_mc(self):
        mock_market_catalogue = mock.Mock()
        self.market.market_catalogue = mock_market_catalogue
        self.assertEqual(self.market.event_id, mock_market_catalogue.event.id)

    def test_event_id_mb(self):
        self.market.market_catalogue = None
        mock_market_book = mock.Mock()
        self.market.market_book = mock_market_book
        self.assertEqual(
            self.market.event_id, mock_market_book.market_definition.event_id
        )

    def test_market_type_mc(self):
        mock_market_catalogue = mock.Mock()
        self.market.market_catalogue = mock_market_catalogue
        self.assertEqual(
            self.market.market_type, mock_market_catalogue.description.market_type
        )

    def test_market_type_mb(self):
        self.market.market_catalogue = None
        mock_market_book = mock.Mock()
        self.market.market_book = mock_market_book
        self.assertEqual(
            self.market.market_type, mock_market_book.market_definition.market_type
        )

    def test_seconds_to_start(self):
        self.market.market_book = None
        mock_market_catalogue = mock.Mock()
        mock_market_catalogue.market_start_time = datetime.datetime.utcfromtimestamp(1)
        self.market.market_catalogue = mock_market_catalogue
        self.assertLess(self.market.seconds_to_start, 0)

    def test_seconds_to_start_market_book(self):
        self.market.market_catalogue = None
        mock_market_book = mock.Mock()
        mock_market_book.market_definition.market_time = (
            datetime.datetime.utcfromtimestamp(1)
        )
        self.market.market_book = mock_market_book
        self.assertLess(self.market.seconds_to_start, 0)

    def test_seconds_to_start_market_catalogue(self):
        self.market.market_book.market_definition.market_time = (
            datetime.datetime.utcfromtimestamp(1)
        )
        self.assertLess(self.market.seconds_to_start, 0)

    def test_seconds_to_start_none(self):
        self.market.market_book = None
        self.market.market_catalogue = None
        self.assertLess(self.market.seconds_to_start, 0)

    def test_elapsed_seconds_closed(self):
        self.assertIsNone(self.market.elapsed_seconds_closed)
        self.market.closed = True
        self.market.date_time_closed = datetime.datetime.utcnow()
        self.assertGreaterEqual(self.market.elapsed_seconds_closed, 0)

    def test_market_start_datetime(self):
        self.assertEqual(
            self.market.market_start_datetime,
            self.mock_market_book.market_definition.market_time,
        )
        self.market.market_book = None
        self.assertEqual(
            self.market.market_start_datetime,
            self.mock_market_catalogue.market_start_time,
        )
        self.market.market_catalogue = None
        self.assertEqual(
            self.market.market_start_datetime, datetime.datetime.utcfromtimestamp(0)
        )

    @mock.patch(
        "flumine.markets.market.Market.market_start_datetime",
        new_callable=mock.PropertyMock,
        return_value=None,
    )
    def test_market_start_hour_minute(self, mock_market_start_datetime):
        self.assertIsNone(self.market.market_start_hour_minute)
        mock_market_start_datetime.return_value = datetime.datetime.utcfromtimestamp(
            12000000000
        )
        self.assertEqual(self.market.market_start_hour_minute, "2120")

    def test_event_name_mc(self):
        mock_market_catalogue = mock.Mock()
        self.market.market_catalogue = mock_market_catalogue
        self.assertEqual(self.market.event_name, mock_market_catalogue.event.name)

    def test_event_name_mb(self):
        self.market.market_catalogue = None
        mock_market_book = mock.Mock()
        self.market.market_book = mock_market_book
        self.assertEqual(
            self.market.event_name, mock_market_book.market_definition.event_name
        )

    def test_country_code_mc(self):
        mock_market_catalogue = mock.Mock()
        self.market.market_catalogue = mock_market_catalogue
        self.assertEqual(
            self.market.country_code, mock_market_catalogue.event.country_code
        )

    def test_country_code_mb(self):
        self.market.market_catalogue = None
        mock_market_book = mock.Mock()
        self.market.market_book = mock_market_book
        self.assertEqual(
            self.market.country_code, mock_market_book.market_definition.country_code
        )

    def test_venue_mc(self):
        mock_market_catalogue = mock.Mock()
        self.market.market_catalogue = mock_market_catalogue
        self.assertEqual(self.market.venue, mock_market_catalogue.event.venue)

    def test_venue_mb(self):
        self.market.market_catalogue = None
        mock_market_book = mock.Mock()
        self.market.market_book = mock_market_book
        self.assertEqual(self.market.venue, mock_market_book.market_definition.venue)

    def test_race_type_mc(self):
        mock_market_catalogue = mock.Mock()
        self.market.market_catalogue = mock_market_catalogue
        self.assertEqual(
            self.market.race_type, mock_market_catalogue.description.race_type
        )

    def test_race_type_mb(self):
        self.market.market_catalogue = None
        mock_market_book = mock.Mock()
        self.market.market_book = mock_market_book
        self.assertEqual(
            self.market.race_type, mock_market_book.market_definition.race_type
        )

    def test_status(self):
        mock_market_book = mock.Mock(status="OPEN")
        self.market.market_book = mock_market_book
        self.assertEqual(self.market.status, mock_market_book.status)

    @mock.patch("flumine.markets.market.Market.event_type_id")
    @mock.patch("flumine.markets.market.Market.event_id")
    def test_cleared(self, mock_event_id, mock_event_type_id):
        mock_client = mock.Mock(commission_base=0.05)
        mock_order = mock.Mock(
            client=mock_client, size_matched=2.00, profit=20, lookup=(1, 2, 3)
        )
        mock_order.simulated.profit = 20
        self.market.blotter["123"] = mock_order
        self.assertEqual(
            self.market.cleared(mock_client),
            {
                "betCount": 1,
                "betOutcome": "WON",
                "commission": 1.0,
                "customerStrategyRef": config.customer_strategy_ref,
                "eventId": mock_event_id,
                "eventTypeId": mock_event_type_id,
                "lastMatchedDate": None,
                "marketId": "1.234",
                "placedDate": None,
                "profit": 20,
                "settledDate": None,
            },
        )

    def test_info(self):
        self.assertEqual(
            self.market.info,
            {
                "market_id": self.market.market_id,
                "event_id": self.market.event_id,
                "event_type_id": self.market.event_type_id,
                "event_name": self.market.event_name,
                "market_type": self.market.market_type,
                "market_start_datetime": str(self.market.market_start_datetime),
                "country_code": self.market.country_code,
                "venue": self.market.venue,
                "race_type": self.market.race_type,
                "orders_cleared": self.market.orders_cleared,
                "market_cleared": self.market.market_cleared,
                "closed": self.market.closed,
            },
        )
