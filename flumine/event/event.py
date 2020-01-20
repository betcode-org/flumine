from enum import Enum


class EventType(Enum):
    TERMINATOR = 0
    # betfair objects
    MARKET_CATALOGUE = 1
    MARKET_BOOK = 2
    CURRENT_ORDERS = 3
    CLEARED_MARKETS = 4
    CLEARED_ORDERS = 5
    # flumine objects
    CLOSE_MARKET = 101
    STRATEGY_RESET = 102
    CUSTOM_EVENT = 103
    NEW_DAY = 104


class QueueType(Enum):
    HANDLER = 1
    ACCOUNT = 2


class BaseEvent:
    EVENT_TYPE: Enum = None
    QUEUE_TYPE: Enum = None

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
