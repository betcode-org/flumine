import os
import socket

simulated = False
simulated_strategy_isolation = True

instance_id = None  # instance id (e.g. AWS ec2 instanceId)

customer_strategy_ref = socket.gethostname()[
    :15
]  # ie. docker container id (used as order customerStrategyRefs)

hostname = customer_strategy_ref

process_id = os.getpid()  # process id of app

current_time = None  # used for simulation

raise_errors = False  # used for call_check_market / call_process_market_book

max_execution_workers = 32  # max number of workers in execution thread pool

async_place_orders = False  # async place orders

# latencies used for simulation
place_latency = 0.120
cancel_latency = 0.170
update_latency = 0.150
replace_latency = 0.280

order_sep = "-"  # customer_order_ref separator

execution_retry_attempts = 10  # cancel attempts when the OrderStream is not connected
