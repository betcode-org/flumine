import os
import socket

simulated = False

hostname = socket.gethostname()[
    :15
]  # ie. docker container id (used as order customerStrategyRefs)

process_id = os.getpid()  # process id of app

current_time = None  # used for backtesting

raise_errors = False  # used for call_check_market / call_process_market_book
