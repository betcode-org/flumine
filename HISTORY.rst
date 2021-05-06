.. :changelog:

Release History
---------------

1.18.6 (2021-05-06)
+++++++++++++++++++

**Improvements**

- Stream retry timeout bumped
- Docs improved

**Libraries**

- black upgraded to 21.5b0
- dependabot native added

1.18.5 (2021-04-26)
+++++++++++++++++++

**Improvements**

- #121 simulation improvements and further validations

**Libraries**

- black upgraded to 21.4b0

1.18.4 (2021-04-20)
+++++++++++++++++++

**Bug Fixes**

- Duplicate Trade logging handled and has_trade added to Blotter

1.18.3 (2021-04-16)
+++++++++++++++++++

**Improvements**

- 503 errors logged as warnings to prevent duplicate log messages propagating through to services such as sentry.io

**Bug Fixes**

- MarketRecorder example updated to handle orjson/speed use

1.18.2 (2021-04-12)
+++++++++++++++++++

**Improvements**

- #217 error handling improvements

**Bug Fixes**

- Blotter live orders mutable bugfix
- MarketRecorder example clean up fix

1.18.1 (2021-04-08)
+++++++++++++++++++

**Improvements**

- `market_type` filter enabled when backtesting markets
- Remove temp logging

**Bug Fixes**

- Validate logging typo

1.18.0 (2021-04-07)
+++++++++++++++++++

**Improvements**

- #404 Multi market processing (concurrent event market processing)
- strategy order placement depreciated (breaking change as per warning version 1.17.0)
- strategy.log_validation_failures depreciated (breaking change as per warning version 1.17.7)
- #185 Cleared order added to order object on closure (@arch4672)
- gzip market catalogue data in marketrecorder.py example

**Bug Fixes**

- Nasty bug fixed in the way live orders are completed when backtesting (has potentially impacted previous tests)
- Trade.create_order now correctly pulls handicap from trade (was defaulting to 0)

1.17.15 (2021-03-25)
+++++++++++++++++++

**Improvements**

- Blotter exposure refactoring out the get_worst_possible_profit method (@jsphon)
- Market recorder example updated to use gzip compression

1.17.14 (2021-03-24)
+++++++++++++++++++

**Improvements**

- Execution / thread pool state logging
- Default market recorder example to not remove files on clean up

1.17.13 (2021-03-22)
+++++++++++++++++++

**Improvements**

- Market recorder mode added to client (@jorgegarcia7)
- Further execution logging (trying to find time)

1.17.12 (2021-03-15)
+++++++++++++++++++

**Improvements**

- Logging control cleanup / docs

**Bug Fixes**

- missing if in process.py to check order status

1.17.11 (2021-03-12)
+++++++++++++++++++

**Improvements**

- order context added

**Bug Fixes**

- Prevent duplicate order logging control calls

1.17.10 (2021-03-12)
+++++++++++++++++++

**Improvements**

- async placeOrder handling added, defaults to False via config.py
- Execution logging improvements

**Bug Fixes**

- Handle race condition (seen daily) where cancel is not correctly update to execution complete

1.17.9 (2021-03-09)
+++++++++++++++++++

**Improvements**

- Remove session close in execution when removing stale sessions (very slow)
- Refactor closure worker to check all closed markets requiring clearing

**Libraries**

- betfairlightweight upgraded to 2.12.1

1.17.8 (2021-03-08)
+++++++++++++++++++

**Improvements**

- Allow kwargs to be passed to `trade.create_order`
- Correct handling off completed offset orders

**Bug Fixes**

- Prevent closure functions being called on a recorder closure

1.17.7 (2021-03-05)
+++++++++++++++++++

**Improvements**

- strategy.log_validation_failures marked for depreciation and logging pushed up to trading control
- strategy.multi_order_trades var added to allow multiple orders to be placed under a single trade
- RunnerContext trades made public
- Docs cleanup and unused trade vars removed
- config.max_workers renamed to max_execution_workers (*breaking change)

**Bug Fixes**

- Prevent double counting of trades if place called more than once

1.17.6 (2021-03-05)
+++++++++++++++++++

**Improvements**

- trade id added to context to prevent race condition and better visibility on live trades

**Bug Fixes**

- incorrect handling of replace on runner context fix (adds to live trade count)

1.17.5 (2021-03-01)
+++++++++++++++++++

**Bug Fixes**

- #382 replace order failure fix (no execute)

1.17.4 (2021-02-26)
+++++++++++++++++++

**Improvements**

- Transaction id and logging added
- max_workers moved to config to allow int to be configurable

1.17.3 (2021-02-25)
+++++++++++++++++++

**Improvements**

- Potential thread pool exhaustion logging added

1.17.2 (2021-02-25)
+++++++++++++++++++

**Improvements**

- Allow patching of stream retry wait arg

**Bug Fixes**

- Incorrect handling of potential exposure in control

1.17.1 (2021-02-24)
+++++++++++++++++++

**Improvements**

- Current and total transactions available from client
- `blotter.strategy_selection_orders` func added (speed improvement on exposure calc)

**Bug Fixes**

- Refactor of client transaction control to correctly apply the 5000 limit

1.17.0 (2021-02-22)
+++++++++++++++++++

**Improvements**

- Major refactor to order placement using Transaction class to allow user control over order placement
- Trading controls executed on place rather than OrderPackage level (Breaking change to controls)
- strategy order placement to be depreciated (Breaking change from version 1.18.0)
- OrderPackage no longer processed through the queue (quicker tick to trade)
- Error correctly raised on duplicate place calls
- Execution worker count bumped

1.16.3 (2021-02-08)
+++++++++++++++++++

**Bug Fixes**

- Minor fix when combining data and market stream strategies

1.16.2 (2021-02-05)
+++++++++++++++++++

**Improvements**

- Blotter strategy orders added for faster lookup
- Strategy name hash cached
- Minor selection_exposure optimisations
- Simulated optimisations

1.16.1 (2021-01-28)
+++++++++++++++++++

**Improvements**

- Various optimisations on pending_packages and low level listener updates
- Cache stream_id when backtesting
- Always run integrations tests (now possible with faster backtesting from bflw 2.12.0)

1.16.0 (2021-01-25)
+++++++++++++++++++

**Improvements**

- bflw changes / further listener optimisations

**Libraries**

- betfairlightweight upgraded to 2.12.0

1.15.4 (2021-01-18)
+++++++++++++++++++

**Improvements**

- Restrict catalogue requests to market version update

**Bug Fixes**

- #192 correctly lapse limit orders

**Libraries**

- betfairlightweight upgraded to 2.11.2

1.15.3 (2021-01-11)
+++++++++++++++++++

**Bug Fixes**

- Correctly handle runner removal / order void for LimitOnClose/MarketOnClose orders

1.15.2 (2021-01-11)
+++++++++++++++++++

**Improvements**

- Order execution args added on place/cancel/update/replace
- License update
- Example update (@lunswor)

**Bug Fixes**

- #358 dynamic keep alive (based on trading client)

**Libraries**

- py3.5 removed from setup.py

1.15.1 (2020-12-28)
+++++++++++++++++++

**Improvements**

- #356 Jupyter logging control added (POC) with info improvements
- #344 lookup cache added and info optimisations
- #327 correctly return orderStatus
- Middleware optimisation by only processing updated runners
- Minor test improvements

**Libraries**

- betfairlightweight upgraded to 2.11.1

1.15.0 (2020-12-07)
+++++++++++++++++++

**Improvements**

- Updates for bflw 2.11.0
- logging improved on orphan orders

**Bug Fixes**

- #347 incorrect adjustment factor (sub 1.01)

**Libraries**

- betfairlightweight upgraded to 2.11.0

1.14.13 (2020-12-05)
+++++++++++++++++++

**Improvements**

- Backtest market catalogue middleware example (@lunswor)
- #344 Initial work on improving calls when subscribed to 5k+ markets

**Bug Fixes**

- #342 market/limit on close order size remaining bug

1.14.12 (2020-11-28)
+++++++++++++++++++

**Improvements**

- 'on_process' function optimised

**Libraries**

- betfairlightweight upgraded to 2.10.2

1.14.11 (2020-11-25)
+++++++++++++++++++

**Improvements**

- Flaky flaky integration tests

**Bug Fixes**

- Missing 'on_process' function (now subclassed)

1.14.10 (2020-11-25)
+++++++++++++++++++

**Bug Fixes**

- Revert removal of `add_stream` (removed by accident)

1.14.9 (2020-11-25)
+++++++++++++++++++

**Improvements**

- Historic stream cleanup for bflw 2.10.1
- Adding logging of order validation

**Libraries**

- betfairlightweight upgraded to 2.10.1

1.14.8 (2020-11-16)
+++++++++++++++++++

**Improvements**

- Config event added and processed on start

**Bug Fixes**

- #320 prevent market on close limit order when below min bsp liability

1.14.7 (2020-11-14)
+++++++++++++++++++

**Improvements**

- Minor bug on initial init with calculate_traded func

1.14.6 (2020-11-13)
+++++++++++++++++++

**Improvements**

- Refactor on calculate_traded func (15% speed increase)

**Bug Fixes**

- Refactoring create_order_from_current, so that it is not dependent on the '-' separator (@jsphon)

1.14.5 (2020-11-11)
+++++++++++++++++++

**Improvements**

- Docs cleanup

**Bug Fixes**

- #318 process customer order ref
- Rounding on order properties

1.14.4 (2020-11-05)
+++++++++++++++++++

**Improvements**

- #310 typing update and bool return added on stream
- add min_bet_validation flag to prevent control checking min size

**Bug Fixes**

- filters out violated orders from being used to calculate the selection exposure (@lunswor)
- handle simulated cancel when size reduction is larger than size remaining
- pass correct size into create replace order based on api response
- #314 Calculates size_remaining from size and size_matched when not set from placeResponse

1.14.3 (2020-11-02)
+++++++++++++++++++

**Improvements**

- size reduction bug

1.14.2 (2020-11-02)
+++++++++++++++++++

**Improvements**

- _process_cleared_orders called on market closure when backtesting / paper trading
- size reduction handling added to simulated execution on cancel
- Add py3.9 actions test

**Libraries**

- betfairlightweight upgraded to 2.10.0 (exchange stream api release 10/11/20)

1.14.1 (2020-10-29)
+++++++++++++++++++

**Improvements**

- #297 add violation msg to order on violation
- Graceful worker shutdown
- Terminate worker example added

**Libraries**

- betfairlightweight upgraded to 2.9.2
- python-json-logger upgraded to 2.0.1

1.14.0 (2020-10-12)
+++++++++++++++++++

**Improvements**

- Prevent MarketBook latency logging when update is from a snap

**Bug Fixes**

- #291 Bug in calculated_unmatched_exposure func

**Libraries**

- betfairlightweight upgraded to 2.9.0 (#248 memory leak)

1.13.1 (2020-10-08)
+++++++++++++++++++

**Improvements**

- Updates the pricerecorder example method parameters (@lunswor)
- #248 Remove runner_context from strategy on market remove
- #287 order separator (jsphon)

1.13.0 (2020-10-05)
+++++++++++++++++++

**Improvements**

- #270 strategy exposure improvements on trading control

**Bug Fixes**

- Handle unhandled exceptions in execution
- Replace now fixed (regression on removal of `order_package.market`
- Backtest process orders now called before strategy calls *impacts backtesting profit*

**Libraries**

- python-json-logger upgraded to 2.0.0

1.12.3 (2020-09-28)
+++++++++++++++++++

**Bug Fixes**

- Missing book / bet_delay in live fix

1.12.2 (2020-09-28)
+++++++++++++++++++

**Bug Fixes**

- #248 completely remove circular reference to market->blotter
- Correct market closure when recording data (raw)

1.12.1 (2020-09-21)
+++++++++++++++++++

**Bug Fixes**

- #275 Laying Limit Orders, Persistence Type MARKET_ON_CLOSE (@jsphon)
- PR added to actions

1.12.0 (2020-09-14)
+++++++++++++++++++

**Improvements**

- #269 latency warning added

**Bug Fixes**

- #248 addition of weakref to try and break circular reference (@synapticarbors) + deletion of each event

**Libraries**

- betfairlightweight upgraded to 2.8.0 (orjson)
- black updated to 20.8b1

1.11.2 (2020-08-28)
+++++++++++++++++++

**Improvements**

- Minor refactor and test improvements on FlumineBacktest
- Tennis/inplayservice worker example added

**Bug Fixes**

- Validates runner is active on placeOrder when simulating (@lunswor)
- Complete.trade moved to when order or trade status updates rather than process.py, previously it was missing any orders that violated when no other orders active

1.11.1 (2020-08-24)
+++++++++++++++++++

**Improvements**

- #187 strategy and trade runner context additions

**Bug Fixes**

- Handling for SP orders on startup
- Bug fix on client control max orders when backtesting

1.11.0 (2020-08-03)
+++++++++++++++++++

**Improvements**

- invested migrated to executable_orders on RunnerContext *breaking change
- Use MarketCatalogue where available for market descriptions
- Create session added, sessions closed and deleted if stale for 200s or more

**Bug Fixes**

- Limit process to limit orders to prevent SP orders from being completed when not + test bug fix

1.10.6 (2020-08-10)
+++++++++++++++++++

**Bug Fixes**

- Prevent closed markets being removed when paper trading
- Fix missing MarketBook from market (closes #FLUMINE-PROD-EE)

1.10.5 (2020-08-04)
+++++++++++++++++++

**Bug Fixes**

- Prevent closed markets being removed when backtesting
- Adds check to check removal_adjustment_factor is not None when processing runner removal (@lunswor)

1.10.4 (2020-08-03)
+++++++++++++++++++

**Improvements**

- updates for bflw 2.7.2

**Libraries**

- betfairlightweight upgraded to 2.7.2

1.10.3 (2020-08-03)
+++++++++++++++++++

**Bug Fixes**

- Handle missing id in raw data (race stream)
- Handle no market passed to market recorder (race stream)

1.10.2 (2020-08-03)
+++++++++++++++++++

**Improvements**

- _process_raw_data refactored to create market objects and call market.closed_market on closure

**Bug Fixes**

- Docs typo (thanks @petercoles)

**Libraries**

- betfairlightweight upgraded to 2.7.1

1.10.1 (2020-07-20)
+++++++++++++++++++

**Bug Fixes**

- Add middleware moved to init, Simulated needs to be the first middleware

1.10.0 (2020-07-20)
+++++++++++++++++++

**Improvements**

- #180 client paper trade now implemented
- #193 initial work on multi client implementation
- #192 simulation improvements with handling on runner removal

1.9.3 (2020-07-17)
+++++++++++++++++++

**Bug Fixes**

- Move remove_markets logic to process_closed_markets (previously not called if no orders)
- Travis remove py3.5

1.9.2 (2020-07-16)
+++++++++++++++++++

**Improvements**

- update_market_notes refactor and move to utils to make patching easier

**Bug Fixes**

- Market.closed now updated when reopened + logging improvements

1.9.1 (2020-07-15)
+++++++++++++++++++

**Improvements**

- #184 package retry on error (limited to 3 with back-off)
- requests.Session now closed and deleted

1.9.0 (2020-07-13)
+++++++++++++++++++

**Improvements**

- #201 requests session kept and reused to reduce latency
- Middleware add/remove market functions added and integrated into Simulated
- Logging improvements

**Libraries**

- betfairlightweight upgraded to 2.6.0

1.8.2 (2020-07-06)
+++++++++++++++++++

**Improvements**

- Previous 'middle' and 'matched' added to simulated

**Bug Fixes**

- Simulated bug fix on when data is not recorded from the beginning
- Client control 'None' bug fix

1.8.1 (2020-06-30)
+++++++++++++++++++

**Bug Fixes**

- Reduce MC count (debugging seg fault)

1.8.0 (2020-06-29)
+++++++++++++++++++

**Improvements**

- Custom historical listener/stream added
- Large order count (per market) optimisations
- #203 client transaction count
- #224 multi market processing

**Bug Fixes**

- #221 RuntimeError: market/order looping

**Libraries**

- betfairlightweight upgraded to 2.5.0

1.7.0 (2020-06-15)
+++++++++++++++++++

**Improvements**

- market_notes added to Trade
- market removed after closed for 3600 seconds
- client.best_price_execution handling added

1.6.8 (2020-06-10)
+++++++++++++++++++

**Improvements**

- Simulated optimisations on matched size/price (@jsphon)

**Libraries**

- betfairlightweight upgraded to 2.4.0

1.6.7 (2020-06-08)
+++++++++++++++++++

**Improvements**

- #185 cleared orders meta implemented
- Order.elapsed_seconds_executable added

1.6.6 (2020-06-08)
+++++++++++++++++++

**Improvements**

- Error handling added to logging control

**Bug Fixes**

- Incorrect event type passed to log_control

1.6.5 (2020-06-08)
+++++++++++++++++++

**Improvements**

- #205 MarketBook publishTime added to simulated.matched / order.execution_complete time added
- Controls error message added
- Info properties improved
- Order/Trade .complete refactored

**Bug Fixes**

- Log order moved to after execution (missing betId)

1.6.4 (2020-06-08)
+++++++++++++++++++

**Improvements**

- Client passed in AccountBalance event
- PublishTime added to order (MarketBook)
- GH Actions fixed

1.6.3 (2020-06-03)
+++++++++++++++++++

**Improvements**

- #178 Client order stream disable/enable
- #179 Info properties

**Bug Fixes**

- #191 missing git config

1.6.2 (2020-06-03)
+++++++++++++++++++

**Improvements**

- #191 Github actions added for testing and deployment

1.6.1 (2020-06-02)
+++++++++++++++++++

**Bug Fixes**

- #195 refactor to prevent RuntimeError

1.6.0 (2020-06-02)
+++++++++++++++++++

**Improvements**

- #175 Update/Replace simulated handling
- Trade context manager added

**Bug Fixes**

- #163 selection exposure improvement
- BetfairExecution replace bugfix

1.5.7 (2020-06-01)
+++++++++++++++++++

**Bug Fixes**

- Sentry uses name in extra so do not override.

1.5.6 (2020-06-01)
+++++++++++++++++++

**Improvements**

- #186 Error handling when calling strategy functions
- Start delay bumped on workers and name changed
- Minor typos / cleanups

1.5.5 (2020-05-29)
+++++++++++++++++++

**Improvements**

- Missing Middleware inheritance
- get_sp added

**Bug Fixes**

- MarketCatalogue missing from Market when logged

1.5.4 (2020-05-22)
+++++++++++++++++++

**Bug Fixes**

- Market close bug

1.5.3 (2020-05-22)
+++++++++++++++++++

**Improvements**

- Market properties added

**Bug Fixes**

- Memory leak in historical stream fixed (queue)
- process_closed_market bug fix in process logic

1.5.2 (2020-05-21)
+++++++++++++++++++

**Bug Fixes**

- pypi bug?

1.5.1 (2020-05-21)
+++++++++++++++++++

**Improvements**

- Worker refactor to make init simpler when adding custom workers

1.5.0 (2020-05-21)
+++++++++++++++++++

**Improvements**

- Logging control added and integrated
- PriceRecorder example added
- Balance polling added
- Cleared Orders/Market polling added
- Trade.notes added
- Middleware moved to flumine level
- SimulatedMiddleware refactored to handle all logic
- Context added to worker functionality

1.4.0 (2020-05-13)
+++++++++++++++++++

**Improvements**

- Simulated execution created (place/cancel only)
- Backtest simulation created and integrated
- patching added, major speed improvements

**Bug Fixes**

- Handicap missing from order
- Client update account details added
- Replace/Update `update_data` fix (now cleared)

**Libraries**

- betfairlightweight upgraded to 2.3.1

1.3.0 (2020-04-28)
+++++++++++++++++++

**Improvements**

- BetfairExecution now live (place/cancel/update/replace)
- Trading and Client controls now live
- Trade/Order logic created and integrated
- OrderPackage created for execution
- Market class created
- process.py created to handle order/trade logic and linking
- Market catalogue worker added
- Blotter created with some initial functions (selection_exposure)
- Strategy runner_context added to handle selection investment
- OrderStream created and integrated

**Bug Fixes**

- Error handling on keep_alive worker added

**Libraries**

- requests added as dependency

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
- _async renamed to `async_` to match bflw
- py3.7 added to travis
- #28 readme update

**Libraries**

- betfairlightweight upgraded to 1.10.2
