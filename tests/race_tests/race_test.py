import unittest

from race import Race

class RaceTests(unittest.TestCase):
    def test_1(self):
        sut = Race(laps=5, start_time=(12, 00, 00))
        self.assertSequenceEqual([], sut.results())

    def test_2(self):
        sut = Race(laps=5, start_time=(12, 00, 00), participants=[7])
        sut.split(7, (12, 10, 00))

        r = sut.results()
        self.assertEquals(1, len(r))

        self.assertEquals(State.RACING, r[0].state)
        self.assertEquals(7, r[0].bib)
        self.assertEquals(1, r[0].laps)

