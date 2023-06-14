import re
import uuid
import json
import logging
import hashlib
import datetime
import functools
from pathlib import Path
from typing import Optional, Tuple, Callable, Union
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
MARKET_ID_REGEX = re.compile(r"1.\d{9}")
EVENT_ID_REGEX = re.compile(r"\d{8}")
STRATEGY_NAME_HASH_LENGTH = 13


def detect_file_type(file_path: Union[str, tuple]) -> str:
    if isinstance(file_path, tuple):
        file_path = file_path[0]
    path_name = Path(file_path).name
    market_match = bool(MARKET_ID_REGEX.match(path_name))
    event_match = bool(EVENT_ID_REGEX.match(path_name))
    if market_match and not event_match:
        return "MARKET"
    elif not market_match and event_match:
        return "EVENT"
    else:
        return "UNKNOWN"


def create_short_uuid() -> str:
    return str(uuid.uuid4())[:8]


def file_line_count(file_path: str) -> int:
    with open(file_path) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def get_file_md(file_dir: Union[str, tuple], value: str) -> Optional[str]:
    # get value from raw streaming file marketDefinition
    if isinstance(file_dir, tuple):
        file_dir = file_dir[0]
    with open(file_dir, "r") as f:
        first_line = f.readline()
        update = json.loads(first_line)
    if "mc" not in update or not isinstance(update["mc"], list) or not update["mc"]:
        return None
    md = update["mc"][0].get("marketDefinition", {})
    return md.get(value)


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


def make_line_prices(min_unit: float, max_unit: float, interval: float) -> list:
    prices = []
    price = min_unit
    while True:
        price += interval
        if price > max_unit:
            break
        else:
            prices.append(price)
    return prices


PRICES = make_prices(MIN_PRICE, CUTOFFS)
PRICES_FLOAT = [float(price) for price in PRICES]
FINEST_PRICES = make_prices(MIN_PRICE, ((1000, 100),))


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


@functools.lru_cache(maxsize=2048)
def price_ticks_away(price: float, n_ticks: int) -> float:
    try:
        price_index = PRICES_FLOAT.index(price)
        new_index = price_index + n_ticks
        if new_index < 0:
            return 1.01
        return PRICES_FLOAT[new_index]
    except IndexError:
        return 1000


def calculate_matched_exposure(mb: list, ml: list) -> Tuple:
    """Calculates exposure based on list
    of (price, size)
    returns the tuple (profit_if_win, profit_if_lose)
    """
    if not mb and not ml:
        return 0.0, 0.0
    back_exp, back_profit, lay_exp, lay_profit = 0, 0, 0, 0
    for p, s in mb:
        back_exp += -s
        back_profit += (p - 1) * s
    for p, s in ml:
        lay_exp += (p - 1) * -s
        lay_profit += s
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
    back_exp, lay_exp = 0, 0
    for p, s in ub:
        back_exp += -s
    for p, s in ul:
        lay_exp += (p - 1) * -s
    return round(lay_exp, 2), round(back_exp, 2)


def wap(matched: list) -> Tuple[float, float]:
    if not matched:
        return 0, 0
    a, b = 0, 0
    for _, p, s in matched:
        a += p * s
        b += s
    if b == 0 or a == 0:
        return 0, 0
    else:
        return round(b, 2), round(a / b, 2)


def call_strategy_error_handling(
    func: Callable, market, market_book: MarketBook
) -> Optional[bool]:
    try:
        return func(market, market_book)
    except FlumineException as e:
        logger.error(
            "FlumineException %s in %s (%s)" % (e, func.__name__, market.market_id),
            exc_info=True,
        )
    except Exception as e:
        logger.critical(
            "Unknown error %s in %s (%s)" % (e, func.__name__, market.market_id),
            exc_info=True,
        )
        if config.raise_errors:
            raise
    return False


def call_middleware_error_handling(middleware, market) -> None:
    try:
        middleware(market)
    except FlumineException as e:
        logger.error(
            "FlumineException %s in %s (%s)" % (e, middleware, market.market_id),
            exc_info=True,
        )
    except Exception as e:
        logger.critical(
            "Unknown error %s in %s (%s)" % (e, middleware, market.market_id),
            exc_info=True,
        )
        if config.raise_errors:
            raise


def call_process_orders_error_handling(strategy, market, strategy_orders: list) -> None:
    try:
        strategy.process_orders(market, strategy_orders)
    except FlumineException as e:
        logger.error(
            "FlumineException %s in %s (%s)" % (e, strategy, market.market_id),
            exc_info=True,
        )
    except Exception as e:
        logger.critical(
            "Unknown error %s in %s (%s)" % (e, strategy, market.market_id),
            exc_info=True,
        )
        if config.raise_errors:
            raise


def call_process_raw_data(strategy, clk: str, publish_time: int, datum: dict) -> None:
    try:
        strategy.process_raw_data(clk, publish_time, datum)
    except FlumineException as e:
        logger.error(
            "FlumineException %s in %s" % (e, strategy),
            exc_info=True,
        )
    except Exception as e:
        logger.critical(
            "Unknown error %s in %s" % (e, strategy),
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
        return "%s,%s,%s" % (
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


def create_time(publish_time: int, id_: str) -> datetime.datetime:
    pt_datetime = datetime.datetime.utcfromtimestamp(publish_time / 1e3)
    event_id, start_time = id_.split(".")
    hour, minute = int(start_time[:2]), int(start_time[2:])
    return pt_datetime.replace(hour=hour, minute=minute, second=0, microsecond=0)
