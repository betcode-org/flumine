import unittest
from unittest import mock

from flumine import utils


class UtilsTest(unittest.TestCase):
    def test_create_short_uuid(self):
        self.assertTrue(utils.create_short_uuid())

    def test_file_line_count(self):
        self.assertGreater(utils.file_line_count(__file__), 10)

    def test_chunks(self):
        self.assertEqual([i for i in utils.chunks([1, 2, 3], 1)], [[1], [2], [3]])
