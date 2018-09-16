class Participant(object):
    def __init__(self, bib, splits, state):
        self._bib = bib
        self._splits = splits
        self._state = state

    @property
    def bib(self):
        return self._bib

    @property
    def splits(self):
        return self._splits

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
