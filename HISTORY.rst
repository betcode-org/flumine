.. :changelog:

Release History
---------------

2.11.4 (2026-01-08)
+++++++++++++++++++

**Libraries**

- betfairlightweight upgraded to 2.21.1

2.11.3 (2026-01-07)
+++++++++++++++++++

**Improvements**

- betdaq 0.10 min bet size added
- simulation move lapse to after calculating any matches

**Bug Fixes**

- reset order to executable when a cancel/update or replace fails
- placed_date add tzinfo so that elapsed seconds can be calculated correctly

2.11.2 (2025-12-19)
+++++++++++++++++++

**Improvements**

- order_stream_conflate_ms added

2.11.1 (2025-12-17)
+++++++++++++++++++

**Bug Fixes**

- 3.14 utc market fix
- seconds_to_start bug when set to 0 seconds
- limit order persistence validation (MarketOnClose when market is inplay or no inplay available)
- correctly update MarketOnClose/LimitOnClose as EXECUTION_COMPLETE once processed

2.11.0 (2025-12-11)
+++++++++++++++++++

**Libraries**

- Add python 3.13 & 3.14

2.10.2 (2025-11-10)
+++++++++++++++++++

**Bug Fixes**

- Handle orders placed outside of flumine (2.10 change)

**Libraries**

- betfairlightweight upgraded to 2.22.0
- betconnect upgraded to 0.3.0

2.10.1 (2025-10-16)
+++++++++++++++++++

**Bug Fixes**

- Improved handling of PLACE profit calculations for dead-heat (@derek-cl)

2.10.0 (2025-09-24)
+++++++++++++++++++

**Improvements**

- Dynamic customer strategy ref *Breaking Change*

2.9.2 (2025-09-18)
+++++++++++++++++++

**Libraries**

- betfairlightweight upgraded to 2.21.2

2.9.1 (2025-09-01)
+++++++++++++++++++

**Improvements**

- BETDAQ cleanup stolen from @lunswor

**Libraries**

- betfairlightweight upgraded to 2.21.1
- betdaq-retail upgraded to 0.2.0

2.9.0 (2025-08-12)
+++++++++++++++++++

**Libraries**

- Remove python 3.8
- betfairlightweight upgraded to 2.21.0
- black upgraded to 25.1.0

2.8.3 (2025-05-20)
+++++++++++++++++++

**Bug Fixes**

- Prevent SSL Lock on streams on initial start

2.8.2 (2025-04-09)
+++++++++++++++++++

**Improvements**

- Add get_trade(trade_id) method to blotter (@mzaja)
- Feature/parallel multi event simulation (@mzaja)

**Bug Fixes**

- #702 reject invalid min fill size (@mzaja)
- #739 reset size remaining on failed order placement (@mzaja)

2.8.1 (2025-04-01)
+++++++++++++++++++

**Bug Fixes**

- BETDAQ update bug

2.8.0 (2025-03-14)
+++++++++++++++++++

**Improvements**

- Add market exposure (@mberk)
- Trade improvements (pending/rm offset_orders)

2.7.1 (2025-02-19)
+++++++++++++++++++

**Libraries**

- betdaq-retail upgraded to 0.1.1

2.7.0 (2025-02-19)
+++++++++++++++++++

**Improvements**

- BETDAQ Retail client integration (account/execution/order only)

**Libraries**

- betdaq-retail 0.1.0 added as dependency

2.6.10 (2025-02-07)
+++++++++++++++++++

**Improvements**

- Process closed market when filter is empty

2.6.9 (2024-01-10)
+++++++++++++++++++

**Libraries**

- betconnect upgraded to 0.2.2

2.6.8 (2024-11-01)
+++++++++++++++++++

**Improvements**

- Bump stream id to 10000 to prevent conflicts on multiple restarts

2.6.7 (2024-11-01)
+++++++++++++++++++

**Improvements**

- Revert `time_updated` changes
- docs fixed

2.6.6 (2024-10-31)
+++++++++++++++++++

**Improvements**

- FlumineStream update to record `time_updated` on each process

2.6.5 (2024-10-23)
+++++++++++++++++++

**Libraries**

- betfairlightweight upgraded to 2.20.4

2.6.4 (2024-10-03)
+++++++++++++++++++

**Libraries**

- betfairlightweight upgraded to 2.20.3

2.6.3 (2024-09-16)
+++++++++++++++++++

**Improvements**

- Add max_inplay_seconds to HistoricListener (@mberk)

**Bug Fixes**

- #766 use order price when calculating matched price with available volumes

2.6.2 (2024-08-22)
+++++++++++++++++++

**Improvements**

- Remove add/start depreciations

**Bug Fixes**

- Fix utils.get_file_md (@mberk)
- Erroneous application of dead-heat rules to profit calculations (@petercoles)

**Libraries**

- black upgraded to 24.8.0

2.6.1 (2024-03-26)
+++++++++++++++++++

**Improvements**

- docs

**Libraries**

- betfairlightweight upgraded to 2.20.2
- betconnect upgraded to 0.2.1
- black upgraded to 24.4.2
- smart-open upgraded to <8
- tenacity upgraded to <8.3.1

2.6.0 (2024-03-11)
+++++++++++++++++++

**Improvements**

- toml file added / repo cleanup

**Bug Fixes**

- Correctly handle sports data files that contain no valid data

**Libraries**

- python 3.12 added
- betfairlightweight upgraded to 2.20.1
- black upgraded to 24.2.0

2.5.10 (2024-02-15)
+++++++++++++++++++

**Bug Fixes**

- Take II on handling US early races

2.5.9 (2024-02-14)
+++++++++++++++++++

**Bug Fixes**

- Correctly handle US races starting early when simulating TPD

2.5.8 (2024-02-12)
+++++++++++++++++++

**Bug Fixes**

- #743 fok multiple issues (@mzaja)

2.5.7 (2024-01-15)
+++++++++++++++++++

**Improvements**

- Add trade elapsed seconds

**Bug Fixes**

- #732 fix process_sports_data for Race events

2.5.6 (2023-12-13)
+++++++++++++++++++

**Improvements**

- Remove LINE_RANGE LTP default

2.5.5 (2023-12-11)
+++++++++++++++++++

**Improvements**

- #725 Remove redundant event logging
- Refactor _process_sports_data to use eventId

**Bug Fixes**

- Correctly handle LINE_RANGE markets within trading controls / blotter / profit / order

2.5.4 (2023-11-13)
+++++++++++++++++++

**Bug Fixes**

- #721 fix invalid customer ref
- Holds off clearing orders until betfair have settled (@lunswor)

**Libraries**

- betfairlightweight upgraded to 2.19.1[speed]
- black upgraded to 23.11.0

2.5.3 (2023-11-06)
+++++++++++++++++++

**Improvements**

- Slack link expires
- More docs

**Bug Fixes**

- #716 simulation NaN sp

**Libraries**

- betfairlightweight upgraded to 2.19.1
- black upgraded to 23.10.1

2.5.2 (2023-10-09)
+++++++++++++++++++

**Improvements**

- Add black pre-commit hook (@mzaja)

**Bug Fixes**

- Handle missing MarketBook when recording sports data

2.5.1 (2023-10-06)
+++++++++++++++++++

**Improvements**

- #703 Store historical stream ids in a set for faster lookup (@mzaja)
- #699 process market catalogue (@mzaja)

**Bug Fixes**

- #706 Fix FOK simulation error, update tests to cover the bug (@mzaja)

**Libraries**

- black upgraded to 23.9.1
- tenacity upgraded to <8.2.4

2.5.0 (2023-10-05)
+++++++++++++++++++

**Improvements**

- #675 provide flumine to add and start methods (@mzaja)
- Lazily evaluate log message parameters (@petedmarsh)
- Change utils.get_file_md to return a MarketDefinition (@petedmarsh)
- Refactor _read_loop to open entire file in ram + remove function calls
- Use raw json for creating order requests (faster)
- uuid4 is faster
- #688 Use smart-open for opening historical files (@petedmarsh)

**Bug Fixes**

- #677 Remove duplicated method call (@mzaja)
- #679 validation reused trades (@mzaja)
- #681 Adds handling of FOK orders status getting stuck (@lunswor)

**Libraries**

- Add [speed] (@petedmarsh)
- Remove py3.7
- betfairlightweight upgraded to 2.19.0

2.4.2 (2023-08-03)
+++++++++++++++++++

**Bug Fixes**

- #674 Update marketCatalogue fix when recording data

2.4.1 (2023-07-25)
+++++++++++++++++++

**Improvements**

- #671 Add process_new_market method to simulation (@mzaja)

2.4.0 (2023-07-24)
+++++++++++++++++++

**Improvements**

- Simulation against available prices now available using config

2.3.7 (2023-07-24)
+++++++++++++++++++

**Improvements**

- #659 Add process_new_market method to BaseStrategy (@mzaja)

**Bug Fixes**

- Log in if client.keep_alive() fails in BetfairClient (@jorgegarcia7)
- Include min_unit price in make_line_prices (@Code0x58)
- #667 Rename strategy info to prevent jsonlogger conflict

**Libraries**

- betconnect upgraded to 0.1.7
- betfairlightweight upgraded to 2.17.3

2.3.6 (2023-04-27)
+++++++++++++++++++

**Bug Fixes**

- #654 Simulated fill or kill bets matched as regular bets (@mzaja)
- Don't check market_start_time for football events (@kwassmuss)

**Libraries**

- black upgraded to 23.3.0

2.3.5 (2023-03-16)
+++++++++++++++++++

**Bug Fixes**

- #650 Fix min_fill_size simulation bug (@mzaja)
- #647 Prevent overfills of the traded in simulated order (@clivewij)
- FK price is None and therefore size is None

**Libraries**

- tenacity upgraded to 8.2.3
- python-json-logger upgraded to 2.0.7
- betconnect upgraded to 0.1.6
- black upgraded to 23.1.0

2.3.4 (2023-02-17)
+++++++++++++++++++

**Improvements**

- #639 simulation fill or kill

**Bug Fixes**

- OrderStream race condition

2.3.3 (2023-02-09)
+++++++++++++++++++

**Libraries**

- betfairlightweight upgraded to 2.17.1

2.3.2 (2023-01-19)
+++++++++++++++++++

**Bug Fixes**

- #629 simulation: async_place_orders prevents order cancellation

2.3.1 (2022-12-01)
+++++++++++++++++++

**Improvements**

- execution_cls added to Client
- market.market_start_hour_minute added

**Bug Fixes**

- Add price ladder definition to limitoncloseorder

**Libraries**

- python 3.11 testing added

2.3.0 (2022-10-27)
+++++++++++++++++++

**Improvements**

- check_sports added to mimic check_market

**Bug Fixes**

- #621 string formating mistypes
- #622 control handle all ladder types

**Libraries**

- betfairlightweight upgraded to 2.17.0
- black upgraded to 22.10.0

2.2.7 (2022-09-29)
+++++++++++++++++++

**Improvements**

- Changes list_cleared_orders error to warning

2.2.6 (2022-09-08)
+++++++++++++++++++

**Bug Fixes**

- #612 simulation replace cancel error fix

**Libraries**

- betconnect upgraded to 0.1.5
- black upgraded to 22.8.0

2.2.5 (2022-08-26)
+++++++++++++++++++

**Improvements**

- `simulated_full_match` added to client

**Libraries**

- betconnect upgraded to 0.1.4

2.2.4 (2022-08-16)
+++++++++++++++++++

**Improvements**

- Add error handling to process_raw_data

**Bug Fixes**

- Correctly set replacement order datetime created

**Libraries**

- betfairlightweight upgraded to 2.16.7
- betconnect upgraded to 0.1.3

2.2.3 (2022-08-01)
+++++++++++++++++++

**Bug Fixes**

- #455 Handle cancel race condition

2.2.2 (2022-07-20)
+++++++++++++++++++

**Improvements**

- Various small improvements to reduce CPU cycles

2.2.1 (2022-07-14)
+++++++++++++++++++

**Improvements**

- #572 SimulatedSportsData middleware and example strategy added
- Remove market added to simulation

**Bug Fixes**

- Handle market removal race condition

**Libraries**

- betfairlightweight upgraded to 2.16.6
- black upgraded to 22.6.0
- python-json-logger upgraded to 2.0.4

2.2.0 (2022-05-17)
+++++++++++++++++++

**Bug Fixes**

- Revert delta order stream

2.1.1 (2022-05-16)
+++++++++++++++++++

**Libraries**

- betfairlightweight upgraded to 2.16.5

2.1.0 (2022-05-13)
+++++++++++++++++++

**Improvements**

- Market `status` added and `markets.open_market_ids` is now open markets only
- Order profit property added
- Order stream output updated orders only (order_updates_only)
- _process_current_orders refactored to reduce duplicate calls

**Bug Fixes**

- #586 loggingcontrol doc strings

2.0.5 (2022-05-05)
+++++++++++++++++++

**Improvements**

- Handle queue event handling optimisations

**Bug Fixes**

- Market event removal on market recording

2.0.4 (2022-04-25)
+++++++++++++++++++

**Bug Fixes**

- Market event removal

2.0.3 (2022-04-25)
+++++++++++++++++++

**Improvements**

- Middleware slim down
- examples cleanup

2.0.2 (2022-04-21)
+++++++++++++++++++

**Improvements**

- Event lookup added to Markets

**Libraries**

- betconnect upgraded to 0.1.2
- black upgraded to 22.3.0

2.0.1 (2022-03-28)
+++++++++++++++++++

**Improvements**

- Client docs improvement
- `stream_running` added and logic cleanup

**Libraries**

- betfairlightweight upgraded to 2.16.4

2.0.0 (2022-03-25)
+++++++++++++++++++

**Improvements**

- #193 multi clients integrated
- backtest -> simulated rename (*breaking change)
- #566 BetConnect client added

**Bug Fixes**

- #567 market_start_datetime fix
- PaperTrade bug fix on `elapsed_time`

**Libraries**

- betfairlightweight upgraded to 2.16.3
- betconnect==0.1.1 requirement added
- python 3.6 removed

1.22.2 (2022-03-24)
+++++++++++++++++++

**Improvements**

- logo / readme update
- single strategy example added

1.22.1 (2022-03-21)
+++++++++++++++++++

**Improvements**

- betcode-org transfer/renames

**Libraries**

- betfairlightweight upgraded to 2.16.2

1.22.0 (2022-02-28)
+++++++++++++++++++

**Improvements**

- #564 sports data functionality added
- blotter lookups updated to lists only (*breaking change)

1.21.6 (2022-02-18)
+++++++++++++++++++

**Improvements**

- blotter lookups updated to lists (order_status)

**Bug Fixes**

- OrderStreams customer_strategy_refs fix when None provided
- Handle null market_filter when creating streams

**Libraries**

- betfairlightweight upgraded to 2.16.1

1.21.5 (2022-02-14)
+++++++++++++++++++

**Improvements**

- PYPI secret update and deploy environment added
- slack group invite updated

**Libraries**

- betfairlightweight upgraded to 2.16.0

1.21.4 (2022-02-08)
+++++++++++++++++++

**Improvements**

- Remove currency parameters hard coding

**Libraries**

- betfairlightweight upgraded to 2.15.4
- black upgraded to 22.1.0

1.21.3 (2022-01-31)
+++++++++++++++++++

**Improvements**

- Each Way simulated profit handled
- ExecutionValidation control to prevent failed requests being sent continuously, not added by default (@lunswor)

**Bug Fixes**

- trading control exposure bug revert

1.21.2 (2022-01-13)
+++++++++++++++++++

**Improvements**

- license update
- strategy warning on duplicate names
- minor optimisations for simulation

1.21.1 (2022-01-10)
+++++++++++++++++++

**Improvements**

- Process end of flumine on exit
- Flumine added as var to `strategy.finish` (*breaking change)

**Bug Fixes**

- #548 handle execution complete during placement delay
- Correctly add order datetimes on restart

1.21.0 (2022-01-06)
+++++++++++++++++++

**Improvements**

- #528 smart matching on passive orders
- #544 market exposure refactor (*breaking change)

**Bug Fixes**

- #528 simulation processing on in flight requests
- #541 handle betTargetSize
- Example typo (@petercoles)

**Libraries**

- black upgraded to 21.12b0

1.20.13 (2021-12-03)
+++++++++++++++++++

**Improvements**

- #527 custom stream funcs / docs added
- #525 UML diagrams added to docs (@shashikhaya)
- `get_order_from_bet_id` optimisation (very slow with high order count)

**Bug Fixes**

- File type regression

**Libraries**

- betfairlightweight upgraded to 2.15.2
- black upgraded to 21.11b1

1.20.12 (2021-11-26)
+++++++++++++++++++

**Improvements**

- Performance docs added

1.20.11 (2021-11-25)
+++++++++++++++++++

**Improvements**

- #528 MarketOnCloseOrders not included in BacktestLoggingControl example
- #531 Include SP values in jupyterloggingcontrol
- MarketRecorder updates (@mberk)

1.20.10 (2021-11-11)
+++++++++++++++++++

**Bug Fixes**

- Missing clk handling in order and race stream

1.20.9 (2021-11-11)
+++++++++++++++++++

**Improvements**

- #522 add clk to output in market recorder (Breaking Change)
- #517 Extend selection exposures to whole market (@petercoles)
- Example strategies updated to remove whitespace on dump (1mb saved per raw file)

**Libraries**

- betfairlightweight upgraded to 2.15.1

1.20.8 (2021-11-01)
+++++++++++++++++++

**Improvements**

- Handle list of market filters in strategy

**Bug Fixes**

- #519 reset real datetime added to allow s3 download (RequestTimeTooSkewed)

**Libraries**

- black upgraded to 21.10b0

1.20.7 (2021-10-25)
+++++++++++++++++++

**Bug Fixes**

- detect_file_type handle tuple

1.20.6 (2021-10-25)
+++++++++++++++++++

**Improvements**

- SimulatedDateTime minor improvement
- detect_file_type added to log warning when backtesting

1.20.5 (2021-10-22)
+++++++++++++++++++

**Libraries**

- relax tenacity pinning >=7.0.0 <=8.0.1

1.20.4 (2021-10-20)
+++++++++++++++++++

**Improvements**

- #511 Make background worker function callable once
- #512 Allow access to real datetime via context manager

**Libraries**

- python 3.10 testing added
- betfairlightweight upgraded to 2.15.0
- black upgraded to 21.9b0

1.20.3 (2021-09-23)
+++++++++++++++++++

**Bug Fixes**

- #486 elapsed_seconds bug when async

**Libraries**

- betfairlightweight upgraded to 2.14.1

1.20.2 (2021-09-20)
+++++++++++++++++++

**Improvements**

- Restrict logging calls based on level to prevent `info` being called (slow)
- Restrict `process` and `take_sp` calls in simulated.py
- lru cache added to `price_ticks_away`

1.20.1 (2021-09-19)
+++++++++++++++++++

**Improvements**

- RaceCache optimisation

**Bug Fixes**

- #499 bugfix on market recording

1.20.0 (2021-09-17)
+++++++++++++++++++

**Improvements**

- Update to use `listener_kwargs` in `_process` rather than `snap`

**Bug Fixes**

- #499 missing market call on closure

**Libraries**

- betfairlightweight upgraded to 2.14.0

1.19.17 (2021-09-14)
+++++++++++++++++++

**Improvements**

- Backtest speed improvements

1.19.16 (2021-09-13)
+++++++++++++++++++

**Improvements**

- Temporary logging added for testing

1.19.15 (2021-09-13)
+++++++++++++++++++

**Improvements**

- Backtest speed improvements
- Raise error in controls when market or marketBook not available

**Bug Fixes**

- async not correctly pulled from config during transaction

1.19.14 (2021-09-10)
+++++++++++++++++++

**Improvements**

- `process_current_orders` optimisation
- `market_version` and `elapsed_seconds_created` added to order
- `OrderStream` logic improvement
- `market.event` refactored to filter on start time as well as eventId (FORECAST limitation)
- Example improvement (@petercoles)

**Bug Fixes**

- Correctly complete order in blotter when live

1.19.13 (2021-09-08)
+++++++++++++++++++

**Improvements**

- #489 countryCode filter added to backtesting
- Renamed config.hostname to config.customer_strategy_ref. This makes the use of the variable more explicit.
- WARNING: This change will affect users who set config.hostname. From this version onwards, they should set config.customer_strategy_ref.
- Docs / logging control updated

**Bug Fixes**

- #487 Backtesting transaction count maxing out (markets not ordered)

**Libraries**

- black upgraded to 21.8b0

1.19.12 (2021-08-27)
+++++++++++++++++++

**Bug Fixes**

- Prevent duplicate EC calls when backtesting

1.19.11 (2021-08-26)
+++++++++++++++++++

**Improvements**

- #480 Correctly simulate ClearedMarket event when backtesting/paper trading

**Libraries**

- betfairlightweight upgraded to 2.13.2

1.19.10 (2021-08-23)
+++++++++++++++++++

**Bug Fixes**

- #478 Listener kwargs / create bugfix

1.19.9 (2021-08-16)
+++++++++++++++++++

**Bug Fixes**

- #476 fixes and docs update for bflw 2.13.1

**Libraries**

- betfairlightweight upgraded to 2.13.1
- tenacity upgraded to 8.0.1

1.19.8 (2021-08-03)
+++++++++++++++++++

**Improvements**

- #472 Add order status and matched filter to blotter
- Assert on trading client lightweight
- OrderDataStream added to allow order stream data to be recorded as per market/race

**Libraries**

- betfairlightweight upgraded to 2.13.0
- black upgraded to 21.7b0
- python-json-logger upgraded to 2.0.2

1.19.7 (2021-07-12)
+++++++++++++++++++

**Improvements**

- #464 get session handling refactor to take oldest session

**Bug Fixes**

- #454 SP nr size adjustment (@jsphon)
- #464 wrong order state after multiple connection reset errors

1.19.6 (2021-07-09)
+++++++++++++++++++

**Improvements**

- #452 transaction force parameter (@flxbe)
- market `date_time_created` added

**Bug Fixes**

- #454 SP nr adjustments (@jsphon)
- Handle missing mc from historic files (@mlabour)

1.19.5 (2021-07-05)
+++++++++++++++++++

**Bug Fixes**

- #453 Replace Orders drop custom separator from order_id field
- Docs typo (@petercoles)

**Libraries**

- betfairlightweight upgraded to 2.12.2
- black upgraded to black==21.6b0

1.19.4 (2021-06-03)
+++++++++++++++++++

**Bug Fixes**

- Updates simulation class to use config latencies

1.19.3 (2021-06-03)
+++++++++++++++++++

**Bug Fixes**

- Set order to be executable after violating on market status  (@lunswor)

1.19.2 (2021-06-03)
+++++++++++++++++++

**Improvements**

- Move simulated latencies to config (@lunswor)
- Add control to validate market status  (@lunswor)

**Bug Fixes**

- MarketRecorder race condition on file load / remove txt only if aged

**Libraries**

- black upgraded to black==21.5b2

1.19.1 (2021-05-27)
+++++++++++++++++++

**Bug Fixes**

- Prevent race condition between execution and order stream

1.19.0 (2021-05-27)
+++++++++++++++++++

**Improvements**

- Process refactor to use current_order status (remove void/lapse to match betfair)
- Examples improvements

1.18.12 (2021-05-21)
+++++++++++++++++++

**Bug Fixes**

- Prevent race condition on executable/execution_complete and new orders

1.18.11 (2021-05-20)
+++++++++++++++++++

**Improvements**

- Market recorder refactored to have a single processor thread to remove blocking

**Bug Fixes**

- Add order stream start delay and snap pickup
- Missing update current order

1.18.10 (2021-05-17)
+++++++++++++++++++

**Bug Fixes**

- Logging control fix, trade event not triggered

1.18.9 (2021-05-17)
+++++++++++++++++++

**Improvements**

- Notes and market notes added to order (potential race condition fix on transaction)

**Bug Fixes**

- #433 Liability persistence types not checked for <= 2 decimal places (@petercoles)

1.18.8 (2021-05-14)
+++++++++++++++++++

**Improvements**

- Simulation optimisations

**Bug Fixes**

- #173 dead heat profit calculation (@lunswor)
- listenerKwargs inplay / MoC / SP orders fix (@jsphon)

**Libraries**

- black upgraded to 21.5b1

1.18.7 (2021-05-10)
+++++++++++++++++++

**Bug Fixes**

- #423 get_exposures() replace fix (@jsphon)

1.18.6 (2021-05-06)
+++++++++++++++++++

**Improvements**

- Stream retry timeout bumped to 60s
- Docs improved
- get_file_md tuple handing (race stream)

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
