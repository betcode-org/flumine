import uuid
import logging

logger = logging.getLogger(__name__)


def create_short_uuid() -> str:
    return str(uuid.uuid4())[:8]


def file_line_count(file_path: str) -> int:
    with open(file_path) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def keep_alive(client) -> None:
    logger.info("Trading client keep_alive worker executing", extra={"client": client})
    if client.betting_client.session_token is None:
        client.login()
    else:
        client.keep_alive()
