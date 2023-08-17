import time
import logging
import betconnect
import betfairlightweight
from betfairlightweight.filters import streaming_market_filter
from pythonjsonlogger import jsonlogger
from collections import defaultdict

from flumine import Flumine, clients, BaseStrategy, utils

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


class ExampleStrategy(BaseStrategy):
    def start(self, flumine) -> None:
        # this data needs to be updated and would ideally be placed inside a worker
        # context placeholder
        self.context["betconnect"] = context = {
            "active_bookmakers": [],
            "active_sports": [],
            "active_regions": [],
            "active_fixtures": [],
            "active_markets": {},  # fixture_id: [market]
            "active_selections": defaultdict(list),  # market_id: [selection]
            "active_fixtures_lookup": {},
        }
        # get betconnect client
        client = self.clients.get_client(
            clients.ExchangeType.BETCONNECT, username="liampa"
        ).betting_client
        # get active bookmakers
        context["active_bookmakers"] = client.betting.active_bookmakers()
        # get active sports
        active_sports = context["active_sports"] = client.betting.active_sports()
        # get the horse racing sport
        horse_racing = [s for s in active_sports if s.name == "Horse Racing"][0]
        # get active regions
        active_regions = context["active_regions"] = client.betting.active_regions(
            sport_id=horse_racing.sport_id
        )
        # get the England region
        active_region = [r for r in active_regions if r.name == "England"][0]
        # get active market types for horse racing
        active_market_types = client.betting.active_market_types(
            sport_id=horse_racing.sport_id
        )
        # get win market type
        win_market_type = [mt for mt in active_market_types if mt.name == "WIN"][0]

        # Active fixtures
        active_fixtures = context["active_fixtures"] = client.betting.active_fixtures(
            sport_id=horse_racing.sport_id, region_id=active_region.region_id
        )
        for fixture in active_fixtures:
            # get markets
            context["active_markets"][
                fixture.fixture_id
            ] = client.betting.active_markets(fixture_id=fixture.fixture_id)
            # get the selections and prices for WIN market
            fixture_selection_prices = client.betting.selections_for_market(
                fixture_id=fixture.fixture_id,
                market_type_id=win_market_type.market_type_id,
                top_price_only=False,
            )
            for selection in fixture_selection_prices:
                context["active_selections"][selection.source_market_id].append(
                    selection
                )
            context["active_fixtures_lookup"][
                (fixture.display_name, fixture.start_date_time)
            ] = fixture.fixture_id

    def check_market_book(self, market, market_book):
        # process_market_book only executed if this returns True
        if market_book.status != "CLOSED" and market.market_catalogue:
            return True

    def process_market_book(self, market, market_book):
        # betconnect_client = self.clients.get_client(
        #     clients.ExchangeType.BETCONNECT, username="username"
        # )

        fixture_id = self.context["betconnect"]["active_fixtures_lookup"][
            (market.venue, market.market_start_datetime)
        ]
        market_id = self.context["betconnect"]["active_markets"][fixture_id][
            0
        ].source_market_id  # todo
        selections_lookup = {
            s.name: s
            for s in self.context["betconnect"]["active_selections"][market_id]
        }
        runner_names = {
            r.selection_id: r.runner_name for r in market.market_catalogue.runners
        }
        for runner in market_book.runners:
            if runner.status == "ACTIVE":
                # betfair
                runner_name = runner_names[runner.selection_id]
                best_back_price = utils.get_price(runner.ex.available_to_back, 0)
                # betconnect
                selection = selections_lookup[runner_name]
                max_price = selection.max_price

                diff = (1 / max_price) - (1 / best_back_price)

                print(runner_name, best_back_price, max_price, round(diff, 3))


framework = Flumine()

# add clients
betfair_client = clients.BetfairClient(betfairlightweight.APIClient("username"))
framework.add_client(betfair_client)

betconnect_client = clients.BetConnectClient(
    betconnect.APIClient("username", "password", "apiKey", "ppURL")
)
framework.add_client(betconnect_client)

strategy = ExampleStrategy(
    market_filter=streaming_market_filter(market_ids=["1.196548740"]),
    streaming_timeout=2,
)
framework.add_strategy(strategy)

framework.run()
