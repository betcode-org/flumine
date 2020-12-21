import os
import json
import logging
from flumine.controls.loggingcontrols import LoggingControl

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
        self.orders = []
        self.filename = os.path.join("/tmp", "orders.json")

    def _process_end_flumine(self, event):
        framework = event.event
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
                self.orders.append(info)
        # save json
        with open(self.filename, "w") as f:
            json.dump(self.orders, f)
        logger.info("Orders processed", extra={"order_count": len(self.orders)})

    def launch(self, argv=None, **kwargs):
        from jupyterlab.labapp import LabApp

        app = LabApp()
        app.launch_instance(argv=argv, **kwargs, notebook_dir="controls")
