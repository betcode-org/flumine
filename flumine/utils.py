import uuid
from betfairlightweight.filters import streaming_market_filter


def create_short_uuid():
    return str(uuid.uuid4())[:8]
