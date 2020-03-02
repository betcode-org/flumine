import unittest
from unittest import mock

from flumine.worker import BackgroundWorker


class BackgroundWorkerTest(unittest.TestCase):
    def setUp(self):
        self.mock_function = mock.Mock()
        self.worker = BackgroundWorker(
            123, self.mock_function, (1, 2), {"hello": "world"}
        )

    def test_init(self):
        self.assertEqual(self.worker.interval, 123)
        self.assertEqual(self.worker.function, self.mock_function)
        self.assertEqual(self.worker.args, (1, 2))
        self.assertEqual(self.worker.kwargs, {"hello": "world"})

    # def test_run(self):
    #     self.worker.run()
