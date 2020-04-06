import unittest
from unittest import mock

from flumine import utils


class UtilsTest(unittest.TestCase):
    def test_create_short_uuid(self):
        self.assertTrue(utils.create_short_uuid())

    def test_file_line_count(self):
        self.assertGreater(utils.file_line_count(__file__), 10)
