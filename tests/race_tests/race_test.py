import unittest

from race import Race, ParticipantState
from race.errors import (
    RaceHasNotStartedYetError,
    BibIsNotRegisteredError,
    BibHasAlreadyFinishedError,
    MalformedTimeStringError,
    SplitTimeIsEarlierThanStartTimeError,
    SplitsAreOutOfOrderError,
)


class RaceTests(unittest.TestCase):
    def test_DoesNotAcceptSplitIfRaceHasNotStartedYet(self):
        some_participant = 7
        sut = Race(
            laps=5,
            participants=[some_participant])
        some_split_time = "12:15:00"
        with self.assertRaises(RaceHasNotStartedYetError):
            sut.split(some_participant, some_split_time)

    def test_DoesNotAcceptSplitIfBibIsNotRegistered(self):
        some_participant = 7
        sut = Race(
            laps=5,
            participants=[some_participant])
        sut.start('12:00:00')
        not_a_participant = 13
        some_split_time = "12:15:00"
        with self.assertRaises(BibIsNotRegisteredError):
            sut.split(not_a_participant, some_split_time)

    def test_DoesNotAcceptSplitIfItIsEarlierThanStartTime(self):
        some_participant = 7
        sut = Race(
            laps=5,
            participants=[some_participant])
        sut.start('12:00:00')
        earlier_than_start = "11:00:00"
        with self.assertRaises(SplitTimeIsEarlierThanStartTimeError):
            sut.split(some_participant, earlier_than_start)

    def test_ResultsTableContainsAllRegisteredParticipants(self):
        participant_count = 3
        sut = Race(
            laps=5,
            participants=list(range(participant_count)))
        sut.start('12:00:00')

        self.assertEqual(participant_count, len(sut.results()))

    def test_ResultsTableHandleOneLap(self):
        some_participant = 7
        sut = Race(
            laps=5,
            participants=[some_participant])
        sut.start('12:00:00')

        split_time = "12:15:00"

        sut.split(some_participant, split_time)

        result = sut.results()[0]

        self.assertEqual(ParticipantState.RACING, result.state)
        self.assertEqual(some_participant, result.bib)
        self.assertEqual(1, result.laps_done)
        self.assertEqual(['00:15:00'], result.lap_times)

    def test_ResultsTableHandleMultipleLaps(self):
        some_participant = 7
        sut = Race(
            laps=3,
            participants=[some_participant])
        sut.start('12:00:00')

        sut.split(some_participant, '12:10:10')
        sut.split(some_participant, '12:15:20')
        sut.split(some_participant, '12:20:00')

        result = sut.results()[0]

        self.assertEqual(ParticipantState.FINISHED, result.state)
        self.assertEqual(3, result.laps_done)
        self.assertSequenceEqual(
            ['00:10:10', '00:05:10', '00:04:40'], result.lap_times)

    def test_DoesNotAcceptSplitIfBibHasAlreadyFinished(self):
        some_participant = 7
        sut = Race(
            laps=3,
            participants=[some_participant])
        sut.start('12:00:00')

        sut.split(some_participant, '12:10:10')
        sut.split(some_participant, '12:15:20')
        sut.split(some_participant, '12:20:00')

        with self.assertRaises(BibHasAlreadyFinishedError):
            excessive_split = '12:25:00'
            sut.split(some_participant, excessive_split)

    def test_DoesNotAcceptDnfIfBibIsNotRegistered(self):
        some_participant = 7
        sut = Race(
            laps=3,
            participants=[some_participant])
        sut.start('12:00:00')

        not_a_participant = 13
        with self.assertRaises(BibIsNotRegisteredError):
            sut.dnf(not_a_participant)

    def test_DoesNotAcceptSplitIfBibHasAlreadyDnf(self):
        some_participant = 7
        sut = Race(
            laps=3,
            participants=[some_participant])
        sut.start('12:00:00')

        sut.split(some_participant, '12:10:00')
        sut.split(some_participant, '12:15:00')

        sut.dnf(some_participant)

        with self.assertRaises(BibHasAlreadyFinishedError):
            sut.split(some_participant, '12:20:00')

    def test_DoesNotAcceptDnfIfBibHasAlreadyFinished(self):
        some_participant = 7
        sut = Race(
            laps=3,
            participants=[some_participant])
        sut.start('12:00:00')

        sut.split(some_participant, '12:10:10')
        sut.split(some_participant, '12:15:20')
        sut.split(some_participant, '12:20:00')

        with self.assertRaises(BibHasAlreadyFinishedError):
            sut.dnf(some_participant)

    def test_DnfRidesHasDnfInResultsTable(self):
        some_participant = 7
        sut = Race(
            laps=3,
            participants=[some_participant])
        sut.start('12:00:00')

        sut.split(some_participant, '12:10:10')
        sut.split(some_participant, '12:15:20')

        sut.dnf(some_participant)

        result = sut.results()[0]

        self.assertEqual(ParticipantState.DNF, result.state)

    def test_DoesNotAcceptsDnfIfRaceHasNotStartedYet(self):
        some_participant = 7
        sut = Race(
            laps=5,
            participants=[some_participant])
        with self.assertRaises(RaceHasNotStartedYetError):
            sut.dnf(some_participant)

    def test_DoesNotAcceptMalformedTimeStrings(self):
        some_participant = 7
        sut = Race(
            laps=5,
            participants=[some_participant])
        sut.start('12:00:00')
        malformed_time_strings = [
            '25:00:00', '12:61:00', '12:00:61',
            '-01:00:00', '12:00',
            'ab:bc:de', '12:00:00,', '12 :00: 00'
        ]
        for malformed_time_string in malformed_time_strings:
            with self.assertRaises(MalformedTimeStringError):
                sut.split(some_participant, malformed_time_string)

    def test_WhileTheRaceIsNotStartedEverybodyWarmsUp(self):
        some_participant = 7
        sut = Race(
            laps=5,
            participants=[some_participant])
        result = sut.results()[0]
        self.assertEqual(ParticipantState.WARMING_UP, result.state)

    def test_TheOneWhoFinishesEarlierStandsHigher(self):
        participant1 = 7
        participant2 = 9
        sut = Race(
            laps=3,
            participants=[participant1, participant2])
        sut.start('12:00:00')
        sut.split(participant1, '12:15:15')
        sut.split(participant2, '12:15:16')
        standings = [result.bib for result in sut.results()]
        self.assertSequenceEqual([participant1, participant2], standings)

    def test_TheOneWhoRidesMoreLapsStandsHigher_1(self):
        participant1 = 7
        participant2 = 9
        sut = Race(
            laps=3,
            participants=[participant1, participant2])
        sut.start('12:00:00')
        sut.split(participant1, '12:15:15')
        standings = [result.bib for result in sut.results()]
        self.assertSequenceEqual([participant1, participant2], standings)

    def test_TheOneWhoRidesMoreLapsStandsHigher_2(self):
        participant1 = 7
        participant2 = 9
        sut = Race(
            laps=3,
            participants=[participant1, participant2])
        sut.start('12:00:00')
        sut.split(participant2, '12:14:00')
        sut.split(participant1, '12:15:00')
        sut.split(participant1, '12:20:00')
        standings = [result.bib for result in sut.results()]
        self.assertSequenceEqual([participant1, participant2], standings)

    def test_TheOneWhoDNFsStandsLower(self):
        participant1 = 7
        participant2 = 9
        sut = Race(
            laps=3,
            participants=[participant1, participant2])
        sut.start('12:00:00')
        sut.split(participant2, '12:10:00')
        sut.split(participant1, '12:12:00')
        sut.split(participant2, '12:15:00')
        sut.dnf(participant2)
        standings = [result.bib for result in sut.results()]
        self.assertSequenceEqual([participant1, participant2], standings)

    def test_LappedRiderRidesLess(self):
        leader = 7
        lapped = 9
        sut = Race(
            laps=3,
            participants=[leader, lapped])
        sut.start('12:00:00')
        sut.split(leader, '12:05:00')
        sut.split(leader, '12:10:00')
        sut.split(lapped, '12:10:00')
        sut.split(leader, '12:15:00')
        sut.split(lapped, '12:20:00')
        lapped_state = sut.results()[1].state
        self.assertEqual(ParticipantState.FINISHED, lapped_state)

    def test_OrderOfSplitsMatters(self):
        some_participant = 7
        other_participant = 9
        sut = Race(
            laps=3,
            participants=[some_participant, other_participant])
        sut.start('12:00:00')

        shuffled_splits = ['12:15:20', '12:10:10']
        sut.split(some_participant, shuffled_splits[0])
        with self.assertRaises(SplitsAreOutOfOrderError):
            sut.split(other_participant, shuffled_splits[1])
