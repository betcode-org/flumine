import logging
from flumine.utils import get_event_ids
from flumine.events.events import CustomEvent

logger = logging.getLogger(__name__)

"""
See examples/tennisexample.py in how
to use this worker for betting.
"""


def poll_in_play_service(context: dict, flumine, event_type_id: str) -> None:
    client = flumine.clients.get_betfair_default()
    event_ids = get_event_ids(flumine.markets, event_type_id=event_type_id)
    for event_id in event_ids:
        response = client.betting_client.in_play_service.get_scores(
            event_ids=[event_id]
        )
        if response is None:
            logger.warning(
                "poll_in_play_service",
                extra={"response": response, "event_id": event_id},
            )
            continue

        for score in response:
            flumine.handler_queue.put(CustomEvent(score, callback))


def callback(flumine, event):
    # update market context
    score = event.event
    for market in flumine.markets:
        if market.event_id == str(score.event_id):
            logger.debug(
                "Updated market {0} with event {1} scores data".format(
                    market.market_id, market.event_id
                )
            )
            market.context["score"] = score
