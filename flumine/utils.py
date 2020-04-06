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


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]
