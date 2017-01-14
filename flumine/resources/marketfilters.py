

class MarketFilter:

    def __init__(self, market_ids=None, bsp_market=None, betting_types=None, event_type_ids=None, event_ids=None,
                 turn_in_play_enabled=None, market_types=None, venues=None, country_codes=None):
        self.market_ids = market_ids or []
        self.bsp_market = bsp_market
        self.betting_types = betting_types or []
        self.event_type_ids = event_type_ids or []
        self.event_ids = event_ids or []
        self.turn_in_play_enabled = turn_in_play_enabled
        self.market_types = market_types or []
        self.venues = venues or []
        self.country_codes = country_codes or []

    @property
    def serialise(self):
        return {
            'marketIds': self.market_ids,
            'bspMarket': self.bsp_market,
            'bettingTypes': self.betting_types,
            'eventTypeIds': self.event_type_ids,
            'eventIds': self.event_ids,
            'turnInPlayEnabled': self.turn_in_play_enabled,
            'marketTypes': self.market_types,
            'venues': self.venues,
            'countryCodes': self.country_codes,
        }


class MarketDataFilter:
    """
    fields: EX_BEST_OFFERS_DISP, EX_BEST_OFFERS, EX_ALL_OFFERS, EX_TRADED,
            EX_TRADED_VOL, EX_LTP, EX_MARKET_DEF, SP_TRADED, SP_PROJECTED
    ladder_levels: 1->10
    """

    def __init__(self, fields=None, ladder_levels=None):
        self.fields = fields or []
        self.ladder_levels = ladder_levels

    @property
    def serialise(self):
        return {
            'fields': self.fields,
            'ladderLevels': self.ladder_levels
        }
