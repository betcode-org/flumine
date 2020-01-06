import unittest
from unittest import mock

from flumine.storage.storageengine import BaseEngine, Local, S3


class BaseEngineTest(unittest.TestCase):
    def setUp(self):
        self.directory = mock.Mock()
        self.engine = BaseEngine(self.directory, 600)

    def test_init(self):
        assert self.engine.NAME is None
        assert self.engine.markets_loaded == []
        assert self.engine.directory == self.directory
        assert self.engine.market_expiration == 600
        assert self.engine.force_update is True

    @mock.patch("flumine.storage.storageengine.BaseEngine.clean_up")
    @mock.patch("flumine.storage.storageengine.BaseEngine.load")
    @mock.patch("flumine.storage.storageengine.BaseEngine.zip_file")
    def test_call(self, mock_zip_file, mock_load, mock_clean_up):
        assert self.engine("1.123", None, "123") is None

    @mock.patch("flumine.storage.storageengine.file_line_count", return_value=2)
    @mock.patch("flumine.storage.storageengine.os")
    @mock.patch("flumine.storage.storageengine.BaseEngine.clean_up")
    @mock.patch("flumine.storage.storageengine.BaseEngine.load")
    @mock.patch("flumine.storage.storageengine.BaseEngine.zip_file", return_value=123)
    def test_call_true(self, mock_zip_file, mock_load, mock_clean_up, mock_os, mock_file_line_count):
        mock_os.os.path.isfile = True
        mock_join = mock.Mock()
        mock_os.path.join = mock_join
        self.engine("1.123", None, "123")

        mock_zip_file.assert_called_with(mock_join(), "1.123", "123")
        mock_load.assert_called_with(123, None)
        mock_clean_up.assert_called_with("123")
        mock_file_line_count.assert_called_with(mock_join())
        assert self.engine.markets_loaded == ["1.123"]
        assert self.engine.markets_loaded_count == 1

    @mock.patch("flumine.storage.storageengine.file_line_count", return_value=1)
    @mock.patch("flumine.storage.storageengine.os")
    @mock.patch("flumine.storage.storageengine.BaseEngine.clean_up")
    @mock.patch("flumine.storage.storageengine.BaseEngine.load")
    @mock.patch("flumine.storage.storageengine.BaseEngine.zip_file", return_value=123)
    def test_call_one_line(self, mock_zip_file, mock_load, mock_clean_up, mock_os, mock_file_line_count):
        mock_os.os.path.isfile = True
        mock_join = mock.Mock()
        mock_os.path.join = mock_join
        self.engine("1.123", None, "123")

        mock_zip_file.assert_not_called()
        mock_load.assert_not_called()
        mock_clean_up.assert_not_called()
        mock_file_line_count.assert_called_with(mock_join())
        assert self.engine.markets_loaded == []
        assert self.engine.markets_loaded_count == 0

    def test_load(self):
        with self.assertRaises(NotImplementedError):
            self.engine.load("", None)

    def test_metadata(self):
        market_definition = {
            "venue": "Menangle",
            "status": "CLOSED",
            "inPlay": True,
            "discountAllowed": True,
            "marketTime": "2017-06-03T07:50:00.000Z",
            "openDate": "2017-06-03T06:40:00.000Z",
            "runners": [
                {
                    "bsp": 4.908084055105574,
                    "sortPriority": 1,
                    "id": 8655916,
                    "adjustmentFactor": 20,
                    "status": "LOSER",
                },
                {
                    "bsp": 4.391726124153355,
                    "sortPriority": 2,
                    "id": 9609057,
                    "adjustmentFactor": 17.857,
                    "status": "LOSER",
                },
                {
                    "bsp": 131.7415596676758,
                    "sortPriority": 3,
                    "id": 8403465,
                    "adjustmentFactor": 1.515,
                    "status": "LOSER",
                },
                {
                    "bsp": 19.528428843872973,
                    "sortPriority": 4,
                    "id": 11000138,
                    "adjustmentFactor": 8.333,
                    "status": "LOSER",
                },
                {
                    "bsp": 160,
                    "sortPriority": 5,
                    "id": 7202563,
                    "adjustmentFactor": 1.515,
                    "status": "LOSER",
                },
                {
                    "bsp": 10.443843781251928,
                    "sortPriority": 6,
                    "id": 8624362,
                    "adjustmentFactor": 6.25,
                    "status": "WINNER",
                },
                {
                    "bsp": 17.5,
                    "sortPriority": 7,
                    "id": 11094377,
                    "adjustmentFactor": 9.091,
                    "status": "LOSER",
                },
                {
                    "bsp": 3.45,
                    "sortPriority": 8,
                    "id": 9204498,
                    "adjustmentFactor": 23.256,
                    "status": "LOSER",
                },
                {
                    "bsp": 298.536131312,
                    "sortPriority": 9,
                    "id": 5596213,
                    "adjustmentFactor": 1.01,
                    "status": "LOSER",
                },
                {
                    "bsp": 147.42486815817654,
                    "sortPriority": 10,
                    "id": 6656290,
                    "adjustmentFactor": 1.515,
                    "status": "LOSER",
                },
                {
                    "bsp": 21.827853476689782,
                    "sortPriority": 11,
                    "id": 7272186,
                    "adjustmentFactor": 4.762,
                    "status": "LOSER",
                },
                {
                    "bsp": 32.93144628533861,
                    "sortPriority": 12,
                    "id": 10470128,
                    "adjustmentFactor": 4.895,
                    "status": "LOSER",
                },
            ],
            "numberOfActiveRunners": 0,
            "complete": True,
            "persistenceEnabled": True,
            "version": 1668900713,
            "betDelay": 1,
            "countryCode": "AU",
            "eventId": "28257726",
            "settledTime": "2017-06-03T07:55:10.000Z",
            "crossMatching": False,
            "marketBaseRate": 8,
            "timezone": "Australia/Sydney",
            "marketType": "WIN",
            "runnersVoidable": False,
            "suspendTime": "2017-06-03T07:50:00.000Z",
            "regulators": ["MR_INT"],
            "bettingType": "ODDS",
            "bspMarket": True,
            "numberOfWinners": 1,
            "bspReconciled": True,
            "turnInPlayEnabled": True,
            "eventTypeId": "7",
        }
        self.engine.create_metadata(market_definition)

    # def test_clean_up(self):
    #     self.engine.directory = '/Users/liampauling/Desktop/fluminetests/FL_A'
    #     self.engine.clean_up('1ff949c8')

    def test_markets_loaded_count(self):
        assert self.engine.markets_loaded_count == 0

    def test_extra(self):
        assert self.engine.extra == {
            "name": self.engine.NAME,
            "markets_loaded": self.engine.markets_loaded,
            "markets_loaded_count": self.engine.markets_loaded_count,
            "directory": self.directory,
        }


class LocalTest(unittest.TestCase):
    def setUp(self):
        self.engine = Local("/tmp")

    def test_init(self):
        assert self.engine.NAME == "LOCAL"
        assert self.engine.directory == "/tmp"

    @mock.patch("flumine.storage.storageengine.shutil")
    def test_load(self, mock_shutil):
        self.engine.load("zip", None)

        mock_shutil.copy.assert_called_with("zip", "/tmp")

    def test_validate_settings(self):
        self.engine.directory = "/sefiodeg"
        with self.assertRaises(OSError):
            self.engine.validate_settings()


class S3Test(unittest.TestCase):
    def setUp(self):
        self.engine = S3("/fdsgjriget")
