from enum import Enum


class Event(Enum):
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


class Queue(Enum):
    HANDLER = 1
    ACCOUNT = 2


class BaseEvent:
    EVENT: Enum = None
    QUEUE: Enum = None

    def __init__(self, event):
        self.event = event

    def __str__(self):
        return "<{0} [{1}]>".format(self.EVENT.name, self.QUEUE.name)


class MarketCatalogueEvent(BaseEvent):
    EVENT = Event.MARKET_CATALOGUE
    QUEUE = Queue.HANDLER


class MarketBookEvent(BaseEvent):
    EVENT = Event.MARKET_BOOK
    QUEUE = Queue.HANDLER


class CurrentOrdersEvent(BaseEvent):
    EVENT = Event.CURRENT_ORDERS
    QUEUE = Queue.HANDLER


class ClearedMarketsEvent(BaseEvent):
    EVENT = Event.CLEARED_MARKETS
    QUEUE = Queue.HANDLER


class ClearedOrdersEvent(BaseEvent):
    EVENT = Event.CLEARED_ORDERS
    QUEUE = Queue.HANDLER


class CloseMarketEvent(BaseEvent):
    EVENT = Event.CLOSE_MARKET
    QUEUE = Queue.HANDLER


class StrategyResetEvent(BaseEvent):
    EVENT = Event.STRATEGY_RESET
    QUEUE = Queue.HANDLER


class CustomEvent(BaseEvent):
    EVENT = Event.CUSTOM_EVENT
    QUEUE = Queue.HANDLER


class NewDayEvent(BaseEvent):
    EVENT = Event.NEW_DAY
    QUEUE = Queue.HANDLER
