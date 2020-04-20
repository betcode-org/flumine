from ..markets.markets import Markets


def process_current_orders(markets: Markets, event):
    print(markets, event)
