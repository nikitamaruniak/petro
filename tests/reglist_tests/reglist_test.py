import unittest
import os

from reglist import Reglist


class ReglistTests(unittest.TestCase):
    def setUp(self):
        test_file_path = os.path.join(
            os.path.dirname(__file__),
            'test.csv')
        self._reglist = Reglist.open(test_file_path)

    def test_category_count(self):
        count = sum(1 for _ in self._reglist.categories)
        self.assertEqual(2, count)

    def test_category_names(self):
        names = [name for (__, name) in self._reglist.categories]
        self.assertEqual(['1. М', '2. Ж'], names)

    def test_participants_by_category(self):
        ps = list(self._reglist.participants(1))
        self.assertEqual(7, len(ps))
        p = [x for x in ps if x.bib == '13']
        self.assertEqual(1, len(p))
        self.assertEqual('Просто Илья', p[0].name)
        self.assertEqual(1, p[0].category_id)
        ps = self._reglist.participants(2)
        p = [x for x in ps if x.name == 'Супер Яна']
        self.assertEqual(1, len(p))
        self.assertEqual(None, p[0].bib)
        self.assertEqual(2, p[0].category_id)

    def test_not_existing_category(self):
        ps = self._reglist.participants(3)
        self.assertEqual(None, ps)

    def test_participant_by_bib(self):
        p = self._reglist.participant('59')
        self.assertEqual('59', p.bib)
        self.assertEqual('Чудо Яна', p.name)
        self.assertEqual(2, p.category_id)

    def test_not_existing_bib(self):
        p = self._reglist.participant('100')
        self.assertEqual(None, p)
