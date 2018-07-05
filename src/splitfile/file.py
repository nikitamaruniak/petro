from .expressions import *
from .parser import parse


class SplitFile(object):

    @classmethod
    def open(cls, file_path):
        expressions = list(parse(_file_iter(file_path)))
        return cls(expressions)

    def __init__(self, expressions):
        self._splits = []
        self._laps = {}
        self._start = {}
        self._finish = {}
        self._reglist = None
        self._errors = []
        self._itt = False
        handlers = {
            SYNTAX_ERROR: SplitFile._handle_syntax_error,
            ITT: SplitFile._handle_itt,
            REGLIST: SplitFile._handle_reglist,
            SPLIT: SplitFile._handle_split,
            LAPS: SplitFile._handle_laps,
            START: SplitFile._handle_start,
            FINISH: SplitFile._handle_finish
        }
        for e in expressions:
            e_type = e[1]
            handler = handlers[e_type]
            handler(self, e)

    def _handle_syntax_error(self, e):
        self._errors.append(e)

    def _handle_itt(self, e):
        if self._itt:
            self._report_syntax_error(e)
        else:
            self._itt = True

    def _handle_reglist(self, e):
        if self._reglist:
            self._report_syntax_error(e)
        else:
            file_path = e[2]
            self._reglist = file_path

    def _handle_split(self, e):
        __, __, bibs, time = e
        for bib in bibs:
            self._splits.append((bib, time))

    def _handle_laps(self, e):
        __, __, categories, nlaps = e
        if not categories:
            raise NotImplementedError
        for c in categories:
            if c in self._laps:
                self._report_syntax_error(e)
            else:
                self._laps[c] = nlaps

    def _handle_start(self, e):
        __, __, categories, time = e
        if not categories:
            raise NotImplementedError
        for c in categories:
            if c in self._start:
                self._report_syntax_error(e)
            else:
                self._start[c] = time

    def _handle_finish(self, e):
        __, __, categories, time = e
        if not categories:
            raise NotImplementedError
        for c in categories:
            if c in self._finish:
                self._report_syntax_error(e)
            else:
                self._finish[c] = time

    def _report_syntax_error(self, e):
        line_number = e[0]
        self._errors.append((line_number, SYNTAX_ERROR))

    @property
    def itt(self):
        return self._itt

    @property
    def reglist(self):
        return self._reglist

    @property
    def splits(self):
        return (s for s in self._splits)

    @property
    def errors(self):
        return (e for e in self._errors)

    @property
    def laps(self):
        for c in self._laps.keys():
            yield (c, self._laps[c])

    @property
    def start(self):
        for c in self._start.keys():
            yield (c, self._start[c])

    @property
    def finish(self):
        for c in self._finish.keys():
            yield (c, self._finish[c])


def _file_iter(file_path):
    with open(file_path, mode='rtU', encoding='utf-8') as f:
        for line in f:
            yield line
