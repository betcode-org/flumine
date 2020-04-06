import time
import threading
import logging

logger = logging.getLogger(__name__)


class BackgroundWorker(threading.Thread):
    def __init__(
        self,
        interval: int,
        function,
        func_args: tuple = None,
        func_kwargs: dict = None,
        **kwargs
    ):
        threading.Thread.__init__(self, daemon=True, **kwargs)
        self.interval = interval
        self.function = function
        self.func_args = func_args if func_args is not None else []
        self.func_kwargs = func_kwargs if func_kwargs is not None else {}

    def run(self) -> None:
        while self.is_alive():
            try:
                self.function(*self.func_args, **self.func_kwargs)
            except Exception as e:
                logger.error("Error in BackgroundWorker {0}: {1}".format(self.name, e))
            time.sleep(self.interval)
