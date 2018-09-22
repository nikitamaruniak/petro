import time

from . import expression


def parse(lines):
    """
    Converts an iterator of strings into an iterator of expressions.

    Syntax:
        Supported expressions:
        <bib> [<bib> ... <bib>] <time>
        start [<cid> ... <cid>] <time>
        finish [<cid> ... <cid>] <time>
        laps [<cid> ... <cid>] <laps>
        reglist <path>
        dnf <bib> <time>
        itt

        bib - bib number - positive number starting from zero.
        cid - category id - positive number starting from 1.
        laps - number of laps - positive number starting from 1.
        path - absolute or relative path to the bikeportal reglist file - string.
        time - time of a day - time representation as a string in the hh:mm:ss format.
        itt - indicates that the race is an Individual Time Trial race.

        Comments:
        Two consecutive dashes mean start of the comment (--). They and
        everything that follows them till the end of line is ignored.

        Whitespace:
        * Empty lines have no special meaning.
        * Trailing spaces and tabs are ignored.
        * Sequences of spaces or tabs have the same meaning as a one symbol.
    # noqa 501
    >>> list(parse(['itt', '', 'foo', 'laps 5', 'start 1 12:13:14', '10 12:35:00', 'dnf 7 12:36:00']))
    [(1, 'itt'), (3, 'error'), (4, 'laps', [], 5), (5, 'start', [1], (12, 13, 14)), (6, 'split', [10], (12, 35, 0)), (7, 'dnf', [7], (12, 36, 0))]
    """
    line_number = 1
    for line in lines:
        t = _token(line)
        if t:
            if not _is_error(t):
                e = _expression(t)
            else:
                e = t
            yield (line_number,) + e
        line_number += 1


def _token(line):
    """
    >>> _token('')
    []
    >>> _token('\t')
    []
    >>> _token('   ')
    []
    >>> _token('   foo')
    ['foo']
    >>> _token('foo  ')
    ['foo']
    >>> _token('foo baz bar')
    ['foo', 'baz', 'bar']

    >>> _token('foo \\'baz bar\\'')
    ['foo', "'baz bar'"]
    >>> _token('foo "baz bar"')
    ['foo', '"baz bar"']
    >>> _token('"  baz  bar "')
    ['"  baz  bar "']
    >>> _token('\\'  baz  bar \\'')
    ["'  baz  bar '"]
    >>> _token('\\'  baz " bar \\'')
    ['\\'  baz " bar \\'']
    >>> _token('"  baz \\' bar "')
    ['"  baz \\' bar "']
    >>> _token('foo"baz')
    ['foo"baz']
    >>> _token('foo "baz')
    ('error',)

    >>> _token('--foo baz bar')
    []
    >>> _token('foo baz-bar')
    ['foo', 'baz-bar']
    >>> _token('foo baz --bar qux')
    ['foo', 'baz']

    >>> _token('foo\\n')
    ['foo']
    """
    n = len(line)
    comment_start = -1
    token_start = -1
    quote_start = -1
    quote_start_type = None
    i = 0
    token = []
    while i < n:
        c = line[i]
        is_white = c == ' ' or c == '\t' or c == '\n'
        if is_white:
            if quote_start == -1 and token_start != -1:
                token.append(line[token_start:i])
                token_start = -1
            i += 1
        elif c == '"' or c == '\'':
            quote_type = 'double' if c == '"' else 'single'
            if quote_start == -1:
                if token_start == -1:
                    quote_start_type = quote_type
                    quote_start = i
                    token_start = i
            elif quote_start_type == quote_type:
                token.append(line[token_start:i + 1])
                token_start = -1
                quote_start = -1
                quote_start_type = None
            i += 1
        elif c == '-':
            if comment_start == -1:
                comment_start = i
            else:
                if token_start != -1:
                    token.append(line[token_start:comment_start])
                    token_start = -1
                i = n
            i += 1
        else:
            if token_start == -1:
                token_start = i
            comment_start = -1
            i += 1

    if token_start != -1:
        if quote_start == -1:
            token.append(line[token_start:])
        else:
            return _error()

    return token


def _strip_comments(line):
    """
    >>> _strip_comments('foo')
    'foo'
    >>> _strip_comments('foo --baz bar')
    'foo '
    """
    comment_start = line.find('--')
    if comment_start != -1:
        line = line[:comment_start]
    return line


def _expression(token):
    for _parser in _parsers:
        e = _parser(token)
        if e is not None:
            return e


def _parse_start(token):
    """
    >>> _parse_start(['foo']) # is None
    >>> _parse_start(['start', '12:00:00'])
    ('start', [], (12, 0, 0))
    >>> _parse_start(['start', '1', '12:00:00'])
    ('start', [1], (12, 0, 0))
    >>> _parse_start(['start', '1', '2', '3', '12:00:00'])
    ('start', [1, 2, 3], (12, 0, 0))
    >>> _parse_start(['start'])
    ('error',)
    >>> _parse_start(['start', 'foo', '12:00:00'])
    ('error',)
    >>> _parse_start(['start', '1', 'foo'])
    ('error',)
    """
    if token[0] != 'start':
        return None
    if len(token) == 1:
        return _error()
    cids = _parse_category_ids(token[1:-1])
    if _is_error(cids):
        return cids
    start_time = _parse_time(token[-1])
    if _is_error(start_time):
        return start_time
    return expression.START, cids, start_time


def _parse_finish(token):
    """
    >>> _parse_finish(['foo']) # is None
    >>> _parse_finish(['finish', '12:00:00'])
    ('finish', [], (12, 0, 0))
    >>> _parse_finish(['finish', '1', '12:00:00'])
    ('finish', [1], (12, 0, 0))
    >>> _parse_finish(['finish', '1', '2', '3', '12:00:00'])
    ('finish', [1, 2, 3], (12, 0, 0))
    >>> _parse_finish(['finish'])
    ('error',)
    >>> _parse_finish(['finish', 'foo', '12:00:00'])
    ('error',)
    >>> _parse_finish(['finish', '1', 'foo'])
    ('error',)
    """
    if token[0] != 'finish':
        return None
    if len(token) == 1:
        return _error()
    cids = _parse_category_ids(token[1:-1])
    if _is_error(cids):
        return cids
    finish_time = _parse_time(token[-1])
    if _is_error(finish_time):
        return finish_time
    return expression.FINISH, cids, finish_time


def _parse_laps(token):
    """
    >>> _parse_laps(['foo']) # is None
    >>> _parse_laps(['laps', '5'])
    ('laps', [], 5)
    >>> _parse_laps(['laps', '1', '5'])
    ('laps', [1], 5)
    >>> _parse_laps(['laps', '1', '2', '3', '5'])
    ('laps', [1, 2, 3], 5)
    >>> _parse_laps(['laps'])
    ('error',)
    >>> _parse_laps(['laps', 'foo', '5'])
    ('error',)
    >>> _parse_laps(['laps', '0'])
    ('error',)
    >>> _parse_laps(['laps', '-2'])
    ('error',)
    >>> _parse_laps(['laps', 'foo'])
    ('error',)
    """
    if token[0] != 'laps':
        return None
    if len(token) == 1:
        return _error()
    cids = _parse_category_ids(token[1:-1])
    if _is_error(cids):
        return cids
    try:
        laps = int(token[-1])
    except ValueError:
        return _error()
    if laps < 1:
        return _error()
    return expression.LAPS, cids, laps


def _parse_split(token):
    """
    >>> _parse_split(['1', '12:00:00'])
    ('split', [1], (12, 0, 0))
    >>> _parse_split(['1', '2', '3', '12:00:00'])
    ('split', [1, 2, 3], (12, 0, 0))
    >>> _parse_split([])
    ('error',)
    >>> _parse_split(['foo'])
    ('error',)
    >>> _parse_split(['1', 'foo'])
    ('error',)
    >>> _parse_split(['foo', '12:00:00'])
    ('error',)
    """
    if len(token) < 2:
        return _error()
    bibs = _parse_bibs(token[:-1])
    if _is_error(bibs):
        return bibs
    split_time = _parse_time(token[-1])
    if _is_error(split_time):
        return split_time
    return expression.SPLIT, bibs, split_time


def _parse_reglist(token):
    """
    >>> _parse_reglist(['foo']) # is None
    >>> _parse_reglist(['reglist', './reglist.csv'])
    ('reglist', './reglist.csv')
    >>> _parse_reglist(['reglist', './RegList.csv'])
    ('reglist', './RegList.csv')
    >>> _parse_reglist(['reglist', '\\'./reg list.csv\\''])
    ('reglist', './reg list.csv')
    >>> _parse_reglist(['reglist', '"./reg list.csv"'])
    ('reglist', './reg list.csv')
    >>> _parse_reglist(['reglist'])
    ('error',)
    >>> _parse_reglist(['reglist', './reglist1.csv', './reglist2.csv'])
    ('error',)
    """
    if token[0] != 'reglist':
        return None
    if len(token) != 2:
        return _error()
    path = token[1]
    path = path.strip('\'')
    path = path.strip('\"')
    return expression.REGLIST, path


def _parse_category_ids(token):
    """
    >>> _parse_category_ids([])
    []
    >>> _parse_category_ids([1])
    [1]
    >>> _parse_category_ids([1, 2, 3])
    [1, 2, 3]
    >>> _parse_category_ids([1, 'foo', 3])
    ('error',)
    >>> _parse_category_ids([1, 0, 3])
    ('error',)
    >>> _parse_category_ids([1, -2, 3])
    ('error',)
    """
    try:
        cids = list(map(int, token))
    except ValueError:
        return _error()
    for cid in cids:
        if cid < 1:
            return _error()
    return cids


def _parse_time(token):
    """
    >>> _parse_time('')
    ('error',)
    >>> _parse_time('foo')
    ('error',)
    >>> _parse_time('24:00:00')
    ('error',)
    >>> _parse_time('25:00:00')
    ('error',)
    >>> _parse_time('00:00:00')
    (0, 0, 0)
    >>> _parse_time('23:59:59')
    (23, 59, 59)
    >>> _parse_time('13:14:15')
    (13, 14, 15)
    """
    try:
        tm = time.strptime(token, '%H:%M:%S')
    except ValueError:
        return _error()
    return tm.tm_hour, tm.tm_min, tm.tm_sec


def _parse_bibs(token):
    """
    >>> _parse_bibs([])
    []
    >>> _parse_bibs([0])
    [0]
    >>> _parse_bibs([1])
    [1]
    >>> _parse_bibs([11])
    [11]
    >>> _parse_bibs([1, 2, 3])
    [1, 2, 3]
    >>> _parse_bibs([1, 'foo', 3])
    ('error',)
    >>> _parse_bibs([1, -2, 3])
    ('error',)
    """
    try:
        bibs = list(map(int, token))
    except ValueError:
        return _error()
    for bib in bibs:
        if bib < 0:
            return _error()
    return bibs


def _parse_itt(token):
    """
    >>> _parse_itt(['itt'])
    ('itt',)
    >>> _parse_itt(['itt', 'foo'])
    ('error',)
    >>> _parse_itt(['itta']) # is None
    """
    if token[0] != 'itt':
        return None

    if len(token) != 1:
        return _error()

    return expression.ITT,


def _parse_dnf(token):
    """
    >>> _parse_dnf(['dnf', '1', '12:00:00'])
    ('dnf', [1], (12, 0, 0))
    >>> _parse_dnf(['dnf', '1', '2', '12:00:00'])
    ('dnf', [1, 2], (12, 0, 0))
    >>> _parse_dnf(['foo', 1, '12:00:00']) # is None
    >>> _parse_dnf(['dnf'])
    ('error',)
    >>> _parse_dnf(['dnf', 'foo', '12:00:00'])
    ('error',)
    >>> _parse_dnf(['dnf', 1, 'foo'])
    ('error',)
    """
    if token[0] != 'dnf':
        return None
    bibs = _parse_bibs(token[1:-1])
    if _is_error(bibs):
        return bibs
    split_time = _parse_time(token[-1])
    if _is_error(split_time):
        return split_time
    return expression.DNF, bibs, split_time


_parsers = [
    _parse_start,
    _parse_finish,
    _parse_laps,
    _parse_reglist,
    _parse_itt,
    _parse_dnf,
    _parse_split,
    lambda _: _error()
]


def _error():
    return expression.SYNTAX_ERROR,


def _is_error(exp):
    return \
        isinstance(exp, tuple) \
        and len(exp) > 0 \
        and exp[0] == expression.SYNTAX_ERROR
