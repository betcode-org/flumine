import uuid
import logging
from betfairlightweight import APIClient

logger = logging.getLogger(__name__)


def create_short_uuid() -> str:
    return str(uuid.uuid4())[:8]


def file_line_count(file_path: str) -> int:
    with open(file_path) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def keep_alive(trading: APIClient, interactive: bool) -> None:
    logger.info(
        "Trading client keep_alive worker executing", extra={"trading": trading}
    )
    if trading.session_token is None:
        if interactive:
            trading.login_interactive()
        else:
            trading.login()
    elif trading.session_expired:
        trading.keep_alive()
