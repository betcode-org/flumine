# Markets

### Market

Within markets you have market objects which contains current up to date market data.

```python
from flumine.markets.market import Market

market: Market

market.market_book

market.market_catalogue
```

### Middleware

It is common that you want to carry about analysis on a market before passing through to strategies, similar to Django's middleware design flumine allows middleware to be executed.

For example backtesting uses [simulated middleware](https://github.com/liampauling/flumine/blob/master/flumine/markets/middleware.py#L15) in order to calculate order matching.

!!! note
    Middleware will be executed in the order it is added.
