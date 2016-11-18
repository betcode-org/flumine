import unittest
from unittest import mock

from flumine.marketfilters.basefilter import MarketDataFilter, MarketFilter


class MarketFilterTest(unittest.TestCase):

    def setUp(self):
        self.market_filter = MarketFilter()

    def test_init(self):
        assert self.market_filter.market_ids == []
        assert self.market_filter.bsp_market is None
        assert self.market_filter.betting_types == []
        assert self.market_filter.event_type_ids == []
        assert self.market_filter.event_ids == []
        assert self.market_filter.turn_in_play_enabled is None
        assert self.market_filter.market_types == []
        assert self.market_filter.venues == []
        assert self.market_filter.country_codes == []

    def test_serialise(self):
        assert self.market_filter.serialise == {
            'marketIds': [],
            'bspMarket': None,
            'bettingTypes': [],
            'eventTypeIds': [],
            'eventIds': [],
            'turnInPlayEnabled': None,
            'marketTypes': [],
            'venues': [],
            'countryCodes': [],
        }


class MarketDataFilterTest(unittest.TestCase):

    def setUp(self):
        self.fields = [1, 2, 3]
        self.ladder_levels = 69
        self.market_filter = MarketDataFilter(self.fields, self.ladder_levels)

    def test_init(self):
        assert self.market_filter.fields == self.fields
        assert self.market_filter.ladder_levels == self.ladder_levels

    def test_serialise(self):
        assert self.market_filter.serialise == {
            'fields': self.fields,
            'ladderLevels': self.ladder_levels
        }
