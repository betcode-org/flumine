from enum import Enum


class EventType(Enum):
    TERMINATOR = "Terminator"
    # betfair objects
    MARKET_CATALOGUE = "MarketCatalogue"
    MARKET_BOOK = "MarketBook"
    RAW_DATA = "Raw streaming data"
    CURRENT_ORDERS = "CurrentOrders"
    CLEARED_MARKETS = "ClearedMarkets"
    CLEARED_ORDERS = "ClearedOrders"
    # flumine objects
    ORDER_PACKAGE = "Order package"
    CLOSE_MARKET = "Closed market"
    STRATEGY_RESET = "Strategy reset"
    CUSTOM_EVENT = "Custom event"
    NEW_DAY = "New day"


class QueueType(Enum):
    HANDLER = "Handler queue"
    ACCOUNT = "Account queue"
    LOGGING = "Logging queue"


class BaseEvent:
    EVENT_TYPE = None
    QUEUE_TYPE = None

    def __init__(self, event):
        self.event = event

    def __str__(self):
        return "<{0} [{1}]>".format(self.EVENT_TYPE.name, self.QUEUE_TYPE.name)


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


class StrategyResetEvent(BaseEvent):
    EVENT_TYPE = EventType.STRATEGY_RESET
    QUEUE_TYPE = QueueType.HANDLER


class CustomEvent(BaseEvent):
    EVENT_TYPE = EventType.CUSTOM_EVENT
    QUEUE_TYPE = QueueType.HANDLER


class NewDayEvent(BaseEvent):
    EVENT_TYPE = EventType.NEW_DAY
    QUEUE_TYPE = QueueType.HANDLER
