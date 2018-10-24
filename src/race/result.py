from .participant_state import ParticipantState


class Result(object):
    def __init__(self, rows):
        self._rows = rows
        pass

    def __iter__(self):
        return iter(self._rows)

    def __getitem__(self, item):
        return self._rows[item]

    def __len__(self):
        return len(self._rows)

    @property
    def riders_on_course(self):
        return sum((
            1
            for r in self._rows
            if r.state == ParticipantState.RACING))
