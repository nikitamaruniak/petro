class RaceHasNotStartedYet(ValueError):
    pass


class BibIsNotRegistered(ValueError):
    pass


class BibHasAlreadyFinished(ValueError):
    pass


class MalformedTimeString(ValueError):
    pass


class SplitTimeIsEarlierThanStartTime(ValueError):
    pass


class SplitsAreOutOfOrder(ValueError):
    pass


class InvalidNumberOfLaps(ValueError):
    pass
