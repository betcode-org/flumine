from enum import Enum


class EventType(Enum):
    TERMINATOR = 0
    # betfair objects
    MARKET_CATALOGUE = 10
    MARKET_BOOK = 20
    RAW_DATA = 30
    CURRENT_ORDERS = 40
    CLEARED_MARKETS = 50
    CLEARED_ORDERS = 60
    # flumine objects
    CLOSE_MARKET = 100
    STRATEGY_RESET = 110
    CUSTOM_EVENT = 120
    NEW_DAY = 130


class QueueType(Enum):
    HANDLER = 10
    ACCOUNT = 20


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
