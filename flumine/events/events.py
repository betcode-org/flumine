import datetime
from enum import Enum


class EventType(Enum):
    CONFIG = "Config"
    TERMINATOR = "Terminator"
    # betfair objects
    MARKET_CATALOGUE = "MarketCatalogue"
    MARKET_BOOK = "MarketBook"
    RAW_DATA = "Raw streaming data"
    CURRENT_ORDERS = "CurrentOrders"
    CLEARED_MARKETS = "ClearedMarkets"
    CLEARED_ORDERS = "ClearedOrders"
    CLEARED_ORDERS_META = "ClearedOrders metadata"
    BALANCE = "Balance"
    # flumine objects
    STRATEGY = "Strategy"
    MARKET = "Market"
    TRADE = "Trade"
    ORDER = "Order"
    ORDER_PACKAGE = "Order package"
    CLOSE_MARKET = "Closed market"
    CUSTOM_EVENT = "Custom event"
    NEW_DAY = "New day"


class QueueType(Enum):
    HANDLER = "Handler queue"
    LOGGING = "Logging queue"


class BaseEvent:  # todo __slots__?
    EVENT_TYPE = None
    QUEUE_TYPE = None

    def __init__(self, event):
        self._time_created = datetime.datetime.utcnow()
        self.event = event

    @property
    def elapsed_seconds(self):
        return (datetime.datetime.utcnow() - self._time_created).total_seconds()

    def __str__(self):
        return "<{0} [{1}]>".format(self.EVENT_TYPE.name, self.QUEUE_TYPE.name)


# HANDLER


class MarketCatalogueEvent(BaseEvent):
    EVENT_TYPE = EventType.MARKET_CATALOGUE
    QUEUE_TYPE = QueueType.HANDLER


class MarketBookEvent(BaseEvent):
    EVENT_TYPE = EventType.MARKET_BOOK
    QUEUE_TYPE = QueueType.HANDLER


class RawDataEvent(BaseEvent):
    EVENT_TYPE = EventType.RAW_DATA
    QUEUE_TYPE = QueueType.HANDLER


class CurrentOrdersEvent(BaseEvent):
    EVENT_TYPE = EventType.CURRENT_ORDERS
    QUEUE_TYPE = QueueType.HANDLER


class ClearedMarketsEvent(BaseEvent):
    EVENT_TYPE = EventType.CLEARED_MARKETS
    QUEUE_TYPE = QueueType.HANDLER


class ClearedOrdersEvent(BaseEvent):
    EVENT_TYPE = EventType.CLEARED_ORDERS
    QUEUE_TYPE = QueueType.HANDLER


class CloseMarketEvent(BaseEvent):
    EVENT_TYPE = EventType.CLOSE_MARKET
    QUEUE_TYPE = QueueType.HANDLER


class CustomEvent(BaseEvent):
    EVENT_TYPE = EventType.CUSTOM_EVENT
    QUEUE_TYPE = QueueType.HANDLER

    def __init__(self, event, callback, *args, **kwargs):
        super(CustomEvent, self).__init__(event)
        self.callback = callback


class NewDayEvent(BaseEvent):
    EVENT_TYPE = EventType.NEW_DAY
    QUEUE_TYPE = QueueType.HANDLER


# LOGGING


class ConfigEvent(BaseEvent):
    EVENT_TYPE = EventType.CONFIG
    QUEUE_TYPE = QueueType.LOGGING


class ClearedOrdersMetaEvent(BaseEvent):
    EVENT_TYPE = EventType.CLEARED_ORDERS_META
    QUEUE_TYPE = QueueType.LOGGING


class BalanceEvent(BaseEvent):
    EVENT_TYPE = EventType.BALANCE
    QUEUE_TYPE = QueueType.LOGGING


class StrategyEvent(BaseEvent):
    EVENT_TYPE = EventType.STRATEGY
    QUEUE_TYPE = QueueType.LOGGING


class MarketEvent(BaseEvent):
    EVENT_TYPE = EventType.MARKET
    QUEUE_TYPE = QueueType.LOGGING


class TradeEvent(BaseEvent):
    EVENT_TYPE = EventType.TRADE
    QUEUE_TYPE = QueueType.LOGGING


class OrderEvent(BaseEvent):
    EVENT_TYPE = EventType.ORDER
    QUEUE_TYPE = QueueType.LOGGING


# both


class TerminationEvent(BaseEvent):
    EVENT_TYPE = EventType.TERMINATOR
    QUEUE_TYPE = QueueType.HANDLER
