import threading
from betfairlightweight import StreamListener


class Flumine:

    def __init__(self, trading, strategies):
        self.trading = trading
        self.strategies = strategies

        self._running = False
        self._socket = None

    def handler(self):
        while self._running:
            pass
        print('end handler')

    def start(self, market_filter, market_data_filter):
        self._check_login()
        self._create_socket()
        self._socket.subscribe_to_markets(
                unique_id=2,
                market_filter=market_filter.serialise,
                market_data_filter=market_data_filter.serialise,
        )
        self._running = True
        threading.Thread(target=self.handler, daemon=True).start()
        self._socket.start(async=True)

    def stop(self):
        self._socket.stop()
        self._running = False

    @property
    def _market_filter(self):
        return 1

    @property
    def _market_data_filter(self):
        return 1

    def _check_login(self):
        if self.trading.session_expired:
            self.trading.login()

    def _create_socket(self):
        self._socket = self.trading.streaming.create_stream(
                unique_id=1,
                description='Flumine Socket'
        )

    def stream_status(self):
        return str(self._socket)

    def __str__(self):
        return '<Flumine [%s]>' % ('running' if self._running else 'not running')
