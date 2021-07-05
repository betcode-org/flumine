import os
import socket

simulated = False

instance_id = None  # instance id (e.g. AWS ec2 instanceId)

hostname = socket.gethostname()[
    :15
]  # ie. docker container id (used as order customerStrategyRefs)

process_id = os.getpid()  # process id of app

current_time = None  # used for backtesting

raise_errors = False  # used for call_check_market / call_process_market_book

max_execution_workers = 32  # max number of workers in execution thread pool

async_place_orders = False  # async place orders

# latencies used for backtesting
place_latency = 0.120
cancel_latency = 0.170
update_latency = 0.150
replace_latency = 0.280

order_sep = "-"  # customer_order_ref separator
