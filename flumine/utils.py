import uuid
from betfairlightweight.filters import streaming_market_filter


def create_short_uuid():
    return str(uuid.uuid4())[:8]


def gb_ie_racing():
    return streaming_market_filter(
        event_type_ids=['7'],
        country_codes=['GB', 'IE'],
        market_types=['WIN'],
    )


def au_racing():
    return streaming_market_filter(
        event_type_ids=['7'],
        country_codes=['AU'],
        market_types=['WIN'],
    )


def us_racing():
    return streaming_market_filter(
        event_type_ids=['7'],
        country_codes=['US'],
        market_types=['WIN'],
    )
