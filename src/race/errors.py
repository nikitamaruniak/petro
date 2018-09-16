class RaceHasNotStartedYetError(ValueError):
    pass


class BibIsNotRegisteredError(ValueError):
    pass


class BibHasAlreadyFinishedError(ValueError):
    pass


class MalformedTimeStringError(ValueError):
    pass


class SplitTimeIsEarlierThanStartTimeError(ValueError):
    pass


class SplitsAreOutOfOrderError(ValueError):
    pass
