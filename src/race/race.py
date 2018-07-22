class Race(object):
    def __init__(self, laps, start_time, participants):
        self._laps = laps
        self._start_time = start_time
        self._participants = participants
        pass

    def split(self, bib, split_time):
        pass

    def results(self):
        return []

class Result(object):
    def __init__(self, position, state, bib, laps):
       self._position = position
       self._state = state
       self._bib = bib
       self._laps = laps
    
    @property
    def position(self):
        return self._position

    @property
    def state(self):
        return self._state

    @property
    def bib(self):
        return self._bib

    @property
    def laps(self):
        return self._laps

class State(object):
    Racing = 'racing'
