# Known Issues and Limitations

## Simulating Dead-Heat Results in PLACE markets

### Problem:
To correctly calculate the profit on a PLACE bet when there were more winners than expected, e.g. the market is '3 TBP' but due to a dead heat there are actually 4 winners, requires knowing which 2 selections were in a dead heat.

[Betfair dead heat rules](https://www.betfair.com/www/GBR/en/aboutUs/Rules.and.Regulations/#dheat)

Unfortunately we do not have this information in the standard market data files, which means that an accurate profit cannot be calculated for these simulated scenarios.

As a result, when simulating PLACE markets, Flumine ignores dead-heat results and calculates profit values for each selection as if no dead heat occurred. This means that the total profit for the market could be over- or under-stated if bets were placed on the dead-heat runners.


----


