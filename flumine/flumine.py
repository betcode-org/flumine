import os
import logging
import threading
from tenacity import retry, wait_exponential
from betfairlightweight import (
    APIClient,
    BetfairError,
)

from .listener import FlumineListener
from .exceptions import (
    RunError,
    StreamError,
)

logger = logging.getLogger(__name__)

# dir used to store all data
FLUMINE_DATA = '/data'


class Flumine:

    def __init__(self, recorder, settings=None, unique_id=1e3):
        self._certificate_login = settings.pop('certificate_login', True) if settings else True
        self.trading = self._create_client(settings)
        self.recorder = recorder
        self.unique_id = unique_id

        self._running = False
        self._socket = None
        self.listener = FlumineListener(recorder)  # output queue hack

    def start(self, heartbeat_ms=None, conflate_ms=None, segmentation_enabled=None, _async=True):
        """Checks trading is logged in, creates socket,
        subscribes to markets, sets running to True and
        starts handler/run threads.
        """
        logger.info('Starting stream: %s' % self.unique_id)
        if self._running:
            raise RunError('Flumine is already running, call .stop() first')
        if _async:
            threading.Thread(
                target=self._run,
                args=(conflate_ms, heartbeat_ms, segmentation_enabled),
                daemon=True
            ).start()
        else:
            self._run(conflate_ms, heartbeat_ms, segmentation_enabled)

    def stop(self):
        """Stops socket, sets running to false
        and socket to None
        """
        logger.info('Stopping stream: %s' % self.unique_id)
        if not self._running:
            raise RunError('Flumine is not running')
        if self._socket:
            self._socket.stop()
        self._running = False
        self._socket = None

    def stream_status(self):
        """Checks sockets status
        """
        return str(self._socket) if self._socket else 'Socket not created'

    @staticmethod
    def _create_client(settings):
        """Returns APIClient based on settings
        or looks for username in os.environ
        """
        if settings:
            return APIClient(
                **settings.get('betfairlightweight')
            )
        else:
            username = os.environ.get('username')
            return APIClient(
                username=username
            )

    @retry(wait=wait_exponential(multiplier=1, min=2, max=20))
    def _run(self, conflate_ms, heartbeat_ms, segmentation_enabled):
        """ Runs socket and catches any errors, will
        attempt reconnect after 2s exponentially backing
        off to 20s.
        """
        self._check_login(force=True)

        self._create_socket()

        if self.recorder.STREAM_TYPE == 'market':
            logger.info('Subscribing to markets')
            try:
                self.unique_id = self._socket.subscribe_to_markets(
                    market_filter=self.recorder.market_filter,
                    market_data_filter=self.recorder.market_data_filter,
                    conflate_ms=conflate_ms,
                    heartbeat_ms=heartbeat_ms,
                    segmentation_enabled=segmentation_enabled,
                    initial_clk=self.listener.initial_clk,
                    clk=self.listener.clk,
                )
            except BetfairError as e:
                logger.error('Betfair subscribe_to_markets error: %s' % e)
                raise
        elif self.recorder.STREAM_TYPE == 'race':
            logger.info('Subscribing to races')
            try:
                self.unique_id = self._socket.subscribe_to_races()
            except BetfairError as e:
                logger.error('Betfair subscribe_to_races error: %s' % e)
                raise
        else:
            raise StreamError('%s is not a valid stream type' % self.recorder.STREAM_TYPE)

        self._running = True
        try:
            logger.info('Starting socket..')
            self._socket.start(_async=False)
        except BetfairError as e:
            logger.error('Betfair error: %s' % e)
            raise
        except Exception as e:
            logger.error('Unknown error: %s' % e)
            raise

    def _check_login(self, force=False):
        """Login if session expired
        """
        if self.trading.session_expired or force:
            if self._certificate_login:
                try:
                    self.trading.login()
                except BetfairError as e:
                    logger.error('Betfair login error: %s' % e)
                    raise
            else:
                try:
                    self.trading.login_interactive()
                except BetfairError as e:
                    logger.error('Betfair login_interactive error: %s' % e)
                    raise

    def _create_socket(self):
        """Creates stream
        """
        logger.info('Creating socket')
        self._socket = self.trading.streaming.create_stream(
            unique_id=self.unique_id,
            description='Flumine Socket',
            listener=self.listener,
            host=self.recorder.HOST,
        )

    @property
    def running(self):
        return True if self._running else False

    @property
    def status(self):
        return 'running' if self._running else 'not running'

    def __repr__(self):
        return '<Flumine>'

    def __str__(self):
        return '<Flumine [%s]>' % self.status
