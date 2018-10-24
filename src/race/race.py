from .errors import (
    RaceHasNotStartedYet,
    BibIsNotRegistered,
    BibHasAlreadyFinished,
    SplitTimeIsEarlierThanStartTime,
    SplitsAreOutOfOrder,
    InvalidNumberOfLaps,
)
from .participant import Participant
from .participant_state import ParticipantState
from .result_row import ResultRow
from .result import Result
from .time_str import (
    time_str_to_datetime,
    timedelta_to_time_str
)


class Race(object):
    def __init__(self, laps, bibs):
        if laps <= 0:
            raise InvalidNumberOfLaps()

        self._laps = laps
        self._start_time_dt = None
        self._start_time_str = None
        self._leader_finished = False
        self._leader_finish_time_dt = None
        self._last_split_time_dt = None

        self._participants = {}
        for bib in set(bibs):
            self._participants[bib] = Participant(
                bib=bib,
                splits=[],
                state=ParticipantState.WARMING_UP,
            )

        self._participants
        self._splits = []

    @property
    def laps(self):
        return self._laps

    def start(self, start_time_str):
        self._start_time_dt = time_str_to_datetime(start_time_str)
        self._start_time_str = start_time_str
        self._last_split_time_dt = self._start_time_dt
        for participant in self._participants.values():
            participant.state = ParticipantState.RACING

    @property
    def start_time(self):
        self._ensure_started()
        return self._start_time_str

    @property
    def started(self):
        return self._start_time_dt is not None

    def split(self, bib, split_time_str):
        self._ensure_started()
        self._ensure_registered(bib)

        split_time_dt = time_str_to_datetime(split_time_str)

        if split_time_dt < self._start_time_dt:
            raise SplitTimeIsEarlierThanStartTime()

        self._ensure_in_order(split_time_dt)
        self._last_split_time_dt = split_time_dt

        participant = self._participants[bib]

        self._ensure_racing(participant)

        participant.splits.append(split_time_dt)

        last_split = participant.splits[-1]
        if len(participant.splits) == self._laps:
            participant.state = ParticipantState.FINISHED
            if not self._leader_finished:
                self._leader_finished = True
                self._leader_finish_time_dt = last_split
            elif last_split < self._leader_finish_time_dt:
                self._leader_finish_time_dt = last_split
        elif (self._leader_finished and
              last_split >= self._leader_finish_time_dt):
            participant.state = ParticipantState.FINISHED

    def _ensure_started(self):
        if not self._start_time_dt:
            raise RaceHasNotStartedYet()

    def _ensure_registered(self, bib):
        if bib not in self._participants:
            raise BibIsNotRegistered()

    def _ensure_racing(self, participant):
        if participant.state != ParticipantState.RACING:
            raise BibHasAlreadyFinished()

    def _ensure_in_order(self, split_time_dt):
        if split_time_dt < self._last_split_time_dt:
            raise SplitsAreOutOfOrder()

    def dnf(self, bib):
        self._ensure_started()
        self._ensure_registered(bib)
        participant = self._participants[bib]
        self._ensure_racing(participant)
        participant.state = ParticipantState.DNF

    @property
    def results(self):
        participants = list(self._participants.values())
        participants.sort(key=self._race_rules)
        rows = [
            self._result_item(position + 1, participant)
            for position, participant in enumerate(participants)]
        return Result(rows)

    def _race_rules(self, participant):
        priority = self._priority_by_state[participant.state]
        laps = len(participant.splits)
        laps_left = self._laps - laps
        if laps == 0:
            last_split = self._start_time_dt
        else:
            last_split = participant.splits[-1]

        return priority, laps_left, last_split

    _priority_by_state = {
        ParticipantState.WARMING_UP: 1,
        ParticipantState.FINISHED: 2,
        ParticipantState.RACING: 3,
        ParticipantState.DNF: 4
    }

    def _result_item(self, position, participant):
        splits = participant.splits
        laps_done = len(splits)
        lap_times = list(map(timedelta_to_time_str, self._lap_times(splits)))
        if len(splits):
            total_time = timedelta_to_time_str(
                splits[-1] - self._start_time_dt)
        else:
            total_time = '00:00:00'
        return ResultRow(
            position=position,
            state=participant.state,
            bib=participant.bib,
            laps_done=laps_done,
            lap_times=lap_times,
            total_time=total_time
        )

    def _lap_times(self, splits):
        laps = []
        prev_time_dt = self._start_time_dt
        for split_dt in splits:
            laps.append(split_dt - prev_time_dt)
            prev_time_dt = split_dt
        return laps
