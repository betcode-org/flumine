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

    def __init__(self, *args, **kwargs):
        super(JupyterLoggingControl, self).__init__(*args, **kwargs)
        self.filename = os.path.join("/tmp", "orders.json")

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
                    info["info.{0}".format(k)] = v
                # info.trade
                trade = info.pop("trade")
                for k, v in trade.items():
                    info["trade.{0}".format(k)] = v
                # info.order_type
                order_type = info.pop("order_type")
                for k, v in order_type.items():
                    info["order_type.{0}".format(k)] = v
                # info.simulated
                simulated = info.pop("simulated")
                for k, v in simulated.items():
                    info["simulated.{0}".format(k)] = v
                orders.append(info)
        # market data
        markets = [market.info for market in framework.markets]
        # strategy data
        strategies = [strategy.info for strategy in framework.strategies]
        # create data
        data = {
            "framework": {"title": "flumine", "version": __version__},
            "strategies": strategies,
            "markets": markets,
            "orders": orders,
        }
        self._create_json(data)

    def _create_json(self, data):
        # save json to file
        with open(self.filename, "w") as f:
            json.dump(data, f)

    def launch(self, argv=None, **kwargs):
        from jupyterlab.labapp import LabApp

        app = LabApp()
        app.launch_instance(argv=argv, **kwargs)
