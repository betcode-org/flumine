import unittest
from unittest import mock

from flumine.storage.storageengine import (
    BaseEngine,
    Local,
)


class BaseEngineTest(unittest.TestCase):

    def setUp(self):
        self.engine = BaseEngine()

    def test_init(self):
        assert self.engine.NAME is None
        assert self.engine.markets_loaded == []
        assert self.engine.markets_loaded_count == 0

    @mock.patch('flumine.storage.storageengine.BaseEngine.clean_up')
    @mock.patch('flumine.storage.storageengine.BaseEngine.load')
    @mock.patch('flumine.storage.storageengine.BaseEngine.zip_file')
    def test_call(self, mock_zip_file, mock_load, mock_clean_up):
        assert self.engine('1.123') is None

    @mock.patch('flumine.storage.storageengine.os')
    @mock.patch('flumine.storage.storageengine.BaseEngine.clean_up')
    @mock.patch('flumine.storage.storageengine.BaseEngine.load')
    @mock.patch('flumine.storage.storageengine.BaseEngine.zip_file', return_value=123)
    def test_call_true(self, mock_zip_file, mock_load, mock_clean_up, mock_os):
        mock_os.os.path.isfile = True
        mock_join = mock.Mock()
        mock_os.path.join = mock_join
        self.engine('1.123')

        mock_zip_file.assert_called_with(mock_join(), '1.123')
        mock_load.assert_called_with(123)
        mock_clean_up.assert_called_with(mock_join(), 123)
        assert self.engine.markets_loaded == ['1.123']
        assert self.engine.markets_loaded_count == 1

    def test_load(self):
        with self.assertRaises(NotImplementedError):
            self.engine.load('')

    @mock.patch('flumine.storage.storageengine.os')
    def test_clean_up(self, mock_os):
        self.engine.clean_up('/tmp/hello', '/tmp/world')

        assert mock_os.remove.call_count == 2


class LocalTest(unittest.TestCase):

    def setUp(self):
        self.engine = Local('/tmp')

    def test_init(self):
        assert self.engine.NAME == 'LOCAL'
        assert self.engine.directory == '/tmp'

    @mock.patch('flumine.storage.storageengine.shutil')
    def test_load(self, mock_shutil):
        self.engine.load('zip')

        mock_shutil.copy.assert_called_with('zip', '/tmp')

    def test_validate_settings(self):
        self.engine.directory = '/sefiodeg'
        with self.assertRaises(OSError):
            self.engine.validate_settings()
