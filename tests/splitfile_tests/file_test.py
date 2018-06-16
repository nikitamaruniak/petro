import unittest
import os

from splitfile import SplitFile

class SplitFile_acceptance_test_unix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_file_path = os.path.join(
            os.path.dirname(__file__),
            'test_unix.split')

        cls._sf = SplitFile.open(test_file_path)
        cls._splits = list(cls._sf.splits)

    def test_errors_count(self):
        self.assertEqual(len(list(self._sf.errors)), 0)

    def test_reglist(self):
        self.assertEqual(self._sf.reglist, 'reglist1251.csv')

    def test_itt(self):
        self.assertFalse(self._sf.itt)

    def test_splits_count(self):
        self.assertEqual(len(self._splits), 169)

    def test_splits_contains(self):
        self.assertIn((32, (11, 41, 45)), self._splits)
        self.assertIn((8, (11, 57, 36)), self._splits)
        self.assertIn((60, (12, 9, 47)), self._splits)

    def test_laps(self):
        self.assertEqual(list(self._sf.laps), [(1, 5), (2, 3)])

    def test_start(self):
        self.assertEqual(list(self._sf.start), [(1, (11, 5, 22)), (2, (11, 6, 30))])

    def test_finish(self):
        self.assertEqual(list(self._sf.finish), [(1, (13, 0, 0)), (2, (13, 0, 0))])
