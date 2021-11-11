import os
import json
import logging
from flumine.controls.loggingcontrols import LoggingControl
from flumine import __version__

logger = logging.getLogger(__name__)

"""
Logging control that allows analysis
of backtesting results once complete.

requirements: jupyterlab, pandas, seaborn

use:
    control = JupyterLoggingControl()
    framework.add_logging_control(control)
    ...
    control.launch()
"""


class JupyterLoggingControl(LoggingControl):
    NAME = "JUPYTER_LOGGING_CONTROL"

    def __init__(
        self, file_name: str = "orders.json", directory: str = "/tmp", *args, **kwargs
    ):
        super(JupyterLoggingControl, self).__init__(*args, **kwargs)
        self.file_name = os.path.join(directory, file_name)

    def _process_end_flumine(self, event):
        framework = event.event
        # order data
        orders = []
        for market in framework.markets:
            for order in market.blotter:
                info = order.info
                # info.info
                _info = info.pop("info")
                for k, v in _info.items():
                    info["info__{0}".format(k)] = v
                # info.trade
                trade = info.pop("trade")
                for k, v in trade.items():
                    info["trade__{0}".format(k)] = v
                # info.order_type
                order_type = info.pop("order_type")
                for k, v in order_type.items():
                    info["order_type__{0}".format(k)] = v
                # info.simulated
                simulated = info.pop("simulated")
                for k, v in simulated.items():
                    info["simulated__{0}".format(k)] = v
                # info.responses
                responses = info.pop("responses")
                for k, v in responses.items():
                    info["responses__{0}".format(k)] = v
                orders.append(info)
        # create data
        data = {
            "framework": {"title": "flumine", "version": __version__},
            "strategies": [strategy.info for strategy in framework.strategies],
            "markets": [market.info for market in framework.markets],
            "orders": orders,
        }
        self._create_json(data)

    def _create_json(self, data):
        # save json to file
        with open(self.file_name, "w") as f:
            json.dump(data, f, separators=(",", ":"))

    @staticmethod
    def launch(self, argv=None, **kwargs):
        from jupyterlab.labapp import LabApp

        app = LabApp()
        app.launch_instance(argv=argv, **kwargs)
