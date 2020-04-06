.. :changelog:

Release History
---------------

1.2.0 (2020-04-06)
+++++++++++++++++++

**Improvements**

- Backtest added and HistoricalStream refactor (single threaded)
- Flumine clients created and integrated
- MarketCatalogue polling worker added

**Libraries**

- betfairlightweight upgraded to 2.3.0

1.1.0 (2020-03-09)
+++++++++++++++++++

**Improvements**

- `context` added to strategy
- `.start` / `.add` refactored to make more sense
- HistoricalStream added and working but will change in the future to not use threads (example added)

**Libraries**

- betfairlightweight upgraded to 2.1.0

1.0.0 (2020-03-02)
+++++++++++++++++++

**Improvements**

- Refactor to trading framework / engine
- Remove recorder/storage engine and replace with 'strategies'
- Market and data streams added
- Background worker class added
- Add docs
- exampleone added

**Libraries**

- betfairlightweight upgraded to 2.0.1
- Add tenacity 5.0.3
- Add python-json-logger 0.1.11

0.9.0 (2020-01-06)
+++++++++++++++++++

**Improvements**

- py3.7/3.8 testing and Black fmt
- main.py update to remove flumine hardcoding
- Remove docker and change to 'main.py' example
- Refactor to local_dir so that it can be overwritten

**Bug Fixes**

- File only loaded if < than 1 line
- FLUMINE_DATA updated to /tmp to prevent permission issues

**Libraries**

- betfairlightweight upgraded to 1.10.4
- Add py3.8 support

0.8.1 (2019-09-30)
+++++++++++++++++++

**Improvements**

- logging improvements (exc_info)
- Python 3.4 removed and 3.7 support added

**Libraries**

- betfairlightweight upgraded to 1.10.3

0.8.0 (2019-09-09)
+++++++++++++++++++

**Improvements**

- black fmt
- _async renamed to async_ to match bflw
- py3.7 added to travis
- #28 readme update

**Libraries**

- betfairlightweight upgraded to 1.10.2
