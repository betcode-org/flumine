import uuid
import logging
import hashlib
from collections import defaultdict
from typing import Optional, Tuple, Callable
from decimal import Decimal, ROUND_HALF_UP
from betfairlightweight.resources.bettingresources import MarketBook, RunnerBook

from . import config
from .exceptions import FlumineException

logger = logging.getLogger(__name__)

CUTOFFS = (
    (2, 100),
    (3, 50),
    (4, 20),
    (6, 10),
    (10, 5),
    (20, 2),
    (30, 1),
    (50, 0.5),
    (100, 0.2),
    (1000, 0.1),
)
MIN_PRICE = 1.01
MAX_PRICE = 1000


def create_short_uuid() -> str:
    return str(uuid.uuid4())[:8]


def file_line_count(file_path: str) -> int:
    with open(file_path) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def chunks(l: list, n: int) -> list:
    for i in range(0, len(l), n):
        yield l[i : i + n]


def create_cheap_hash(txt: str, length: int = 15) -> str:
    # This is just a hash for debugging purposes.
    #    It does not need to be unique, just fast and short.
    # https://stackoverflow.com/questions/14023350
    hash_ = hashlib.sha1()
    hash_.update(txt.encode())
    return hash_.hexdigest()[:length]


def as_dec(value):
    return Decimal(str(value))


def arange(start, stop, step):
    while start < stop:
        yield start
        start += step


def make_prices(min_price, cutoffs):
    prices = []
    cursor = as_dec(min_price)
    for cutoff, step in cutoffs:
        prices.extend(arange(as_dec(cursor), as_dec(cutoff), as_dec(1 / step)))
        cursor = cutoff
    prices.append(as_dec(MAX_PRICE))
    return prices


PRICES = make_prices(MIN_PRICE, CUTOFFS)


def get_nearest_price(price, cutoffs=CUTOFFS):
    if price <= MIN_PRICE:
        return MIN_PRICE
    if price > MAX_PRICE:
        return MAX_PRICE
    price = as_dec(price)
    for cutoff, step in cutoffs:
        if price < cutoff:
            break
    step = as_dec(step)
    return float((price * step).quantize(2, ROUND_HALF_UP) / step)


def get_price(data: list, level: int) -> Optional[float]:
    try:
        return data[level]["price"]
    except KeyError:
        return
    except IndexError:
        return
    except TypeError:
        return


def get_size(data: list, level: int) -> Optional[float]:
    try:
        return data[level]["size"]
    except KeyError:
        return
    except IndexError:
        return
    except TypeError:
        return


def get_sp(runner: RunnerBook) -> Optional[float]:
    if isinstance(runner.sp, list):
        return
    elif runner.sp is None:
        return
    elif runner.sp.actual_sp == "NaN":
        return
    else:
        return runner.sp.actual_sp


def price_ticks_away(price: float, n_ticks: int) -> float:
    try:
        price_index = PRICES.index(as_dec(price))
        if price_index + n_ticks < 0:
            return 1.01
        return float(PRICES[price_index + n_ticks])
    except IndexError:
        return 1000


# todo LRU cache?
# JH: LRU cache does not work with list inputs as they are unhashable.
#     So might need to refactor mb and ml into tuples.
def calculate_matched_exposure(mb: list, ml: list) -> Tuple:
    """Calculates exposure based on list
    of (price, size)
    returns the tuple (profit_if_win, profit_if_lose)
    """
    if not mb and not ml:
        return 0.0, 0.0
    back_exp = sum(-i[1] for i in mb)
    back_profit = sum((i[0] - 1) * i[1] for i in mb)
    lay_exp = sum((i[0] - 1) * -i[1] for i in ml)
    lay_profit = sum(i[1] for i in ml)
    _win = back_profit + lay_exp
    _lose = lay_profit + back_exp
    return round(_win, 2), round(_lose, 2)


def calculate_unmatched_exposure(ub: list, ul: list) -> Tuple:
    """Calculates worse-case exposure based on list
    of (price, size)
    returns the tuple (profit_if_win, profit_if_lose)

    The worst case profit_if_win arises if all lay bets are matched and the selection wins.
    The worst case profit_if_lose arises if all back bets are matched and the selection loses.

    """
    if not ub and not ul:
        return 0.0, 0.0
    back_exp = sum(-i[1] for i in ub)
    lay_exp = sum((i[0] - 1) * -i[1] for i in ul)
    return round(lay_exp, 2), round(back_exp, 2)


# todo LRU cache?
def wap(matched: list) -> Tuple[float, float]:
    if not matched:
        return 0, 0
    a, b = 0, 0
    for match in matched:
        a += match[1] * match[2]
        b += match[2]
    if b == 0 or a == 0:
        return 0, 0
    else:
        return round(b, 2), round(a / b, 2)


def call_check_market(
    strategy_check_market: Callable, market, market_book: MarketBook
) -> bool:
    try:
        return strategy_check_market(market, market_book)
    except FlumineException as e:
        logger.error(
            "FlumineException %s in strategy_check_market %s %s"
            % (e, strategy_check_market, market.market_id),
            exc_info=True,
        )
    except Exception as e:
        logger.critical(
            "Unknown error %s in strategy_check_market %s %s"
            % (e, strategy_check_market, market.market_id),
            exc_info=True,
        )
        if config.raise_errors:
            raise
    return False


def call_process_market_book(
    strategy_process_market_book: Callable, market, market_book: MarketBook
) -> None:
    try:
        strategy_process_market_book(market, market_book)
    except FlumineException as e:
        logger.error(
            "FlumineException %s in strategy_process_market_book %s %s"
            % (e, strategy_process_market_book, market.market_id),
            exc_info=True,
        )
    except Exception as e:
        logger.critical(
            "Unknown error %s in strategy_process_market_book %s %s"
            % (e, strategy_process_market_book, market.market_id),
            exc_info=True,
        )
        if config.raise_errors:
            raise


def get_runner_book(
    market_book: MarketBook, selection_id: int, handicap=0
) -> Optional[RunnerBook]:
    """Returns runner book based on selection id."""
    for runner_book in market_book.runners:
        if (
            runner_book.selection_id == selection_id
            and runner_book.handicap == handicap
        ):
            return runner_book


def get_market_notes(market, selection_id: int) -> Optional[str]:
    """Returns a string of notes for a runner,
    currently 'back,lay,last_price_traded'
    """
    runner = get_runner_book(market.market_book, selection_id)
    if runner:
        return "{0},{1},{2}".format(
            get_price(runner.ex.available_to_back, 0),
            get_price(runner.ex.available_to_lay, 0),
            runner.last_price_traded,
        )


def get_event_ids(markets: list, event_type_id: str) -> list:
    event_ids = []
    for market in markets:
        if not market.closed and market.event_type_id == event_type_id:
            event_ids.append(market.event_id)
    return list(set(event_ids))
