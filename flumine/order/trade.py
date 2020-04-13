import uuid


class Trade:
    def __init__(
        self, market_id: str, selection_id: int, strategy, fill_kill, green, stop
    ):
        self.id = uuid.uuid1()
        self.market_id = market_id
        self.selection_id = selection_id
        self.strategy = strategy
        self.fill_kill = fill_kill
        self.green = green
        self.stop = stop
        self.orders = []  # all orders linked to trade
