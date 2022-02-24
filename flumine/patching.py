"""
django style `lazy` object creation, the main bulk of processing
is turning {priceSize} into <PriceSize> objects but this is
pointless a lot of the time as the object is not used or can be
handled as a dict instead.

The inclusion of slots further reduces the processing time as well
as reducing memory.

This optimisation will improve normal streaming as well as
simulation, with more speed, less CPU + ram and minimal reduction
in usability.
"""


class SP:
    __slots__ = [
        "near_price",
        "far_price",
        "actual_sp",
        "back_stake_taken",
        "lay_liability_taken",
    ]

    def __init__(
        self,
        nearPrice: float = None,
        farPrice: float = None,
        backStakeTaken: list = None,
        layLiabilityTaken: list = None,
        actualSP: float = None,
    ):
        self.near_price = nearPrice
        self.far_price = farPrice
        self.actual_sp = actualSP
        self.back_stake_taken = backStakeTaken
        self.lay_liability_taken = layLiabilityTaken


class EX:
    __slots__ = ["available_to_back", "available_to_lay", "traded_volume"]

    def __init__(
        self,
        availableToBack: list = None,
        availableToLay: list = None,
        tradedVolume: list = None,
    ):
        self.available_to_back = availableToBack
        self.available_to_lay = availableToLay
        self.traded_volume = tradedVolume
