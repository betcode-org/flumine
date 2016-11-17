

class Flumine:

    def __init__(self, trading, strategies):
        self.trading = trading
        self.strategies = strategies

        self._socket = None

    def start(self, market_filter, market_data_filter):
        self._check_login()
        self._create_socket()

        self._socket.subscribe_to_markets(unique_id=2,
                                          market_filter=market_filter,
                                          market_data_filter=market_data_filter)
        self._socket.start(async=True)

    def stop(self):
        self._socket.stop()

    def _check_login(self):
        if self.trading.session_expired:
            self.trading.login()

    def _create_socket(self):
        self._socket = self.trading.streaming.create_stream(
                unique_id=1,
                description='Flumine Socket'
        )

    def __str__(self):
        return '<Flumine>'
