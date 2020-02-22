import time
import threading
import logging

logger = logging.getLogger(__name__)


class BackgroundWorker(threading.Thread):
    def __init__(
        self, interval: int, function, args: tuple = None, kwargs: dict = None
    ):
        threading.Thread.__init__(self, daemon=True, name=self.__class__.__name__)
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}

    def run(self) -> None:
        while self.is_alive():
            try:
                self.function(*self.args, **self.kwargs)
            except Exception as e:
                logger.error("Error in BackgroundWorker {0}: {1}".format(self.name, e))
            time.sleep(self.interval)
