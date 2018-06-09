from .expressions import *

def parse(lines):
    '''
    Converts an iterator of strings into an iterator of expressions.

    Syntax:
        Supported expressions:
        <bib> [<bib> ... <bib>] <time>
        start [<cid> ... <cid>] <time>
        laps [<cid> ... <cid>] <laps>
        reglist <path>
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

    >>> list(parse(['itt', '', 'foo', 'laps 5', 'start 1 12:13:14', '10 12:35:00']))
    [(1, 'itt'), (3, 'error'), (4, 'laps', [], 5), (5, 'start', [1], (12, 13, 14)), (6, 'split', [10], (12, 35, 0))]
    '''
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
    '''
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
    '''
    n = len(line)
    comment_start = -1
    token_start = -1
    quote_start = -1
    quote_start_type = None
    doublequote_start = -1
    i = 0
    token = []
    while i < n:
        c = line[i]
        is_white = c == ' ' or c == '\t'
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
    '''
    >>> _strip_comments('foo')
    'foo'
    >>> _strip_comments('foo --baz bar')
    'foo '
    '''
    comment_start = line.find('--')
    if comment_start != -1:
        line = line[:comment_start]
    return line

def _expression(token):
    for _parser in _parsers:
        e = _parser(token)
        if e is not None:
            return e

def _parseStart(token):
    '''
    >>> _parseStart(['foo']) # is None
    >>> _parseStart(['start', '12:00:00'])
    ('start', [], (12, 0, 0))
    >>> _parseStart(['start', '1', '12:00:00'])
    ('start', [1], (12, 0, 0))
    >>> _parseStart(['start', '1', '2', '3', '12:00:00'])
    ('start', [1, 2, 3], (12, 0, 0))
    >>> _parseStart(['start'])
    ('error',)
    >>> _parseStart(['start', 'foo', '12:00:00'])
    ('error',)
    >>> _parseStart(['start', '1', 'foo'])
    ('error',)
    '''
    if token[0] != 'start':
        return None
    if len(token) == 1:
        return _error()
    cids = _parseCategoryIds(token[1:-1])
    if _is_error(cids):
        return cids
    time = _parseTime(token[-1])
    if _is_error(time):
        return time
    return (START, cids, time)

def _parseLaps(token):
    '''
    >>> _parseLaps(['foo']) # is None
    >>> _parseLaps(['laps', '5'])
    ('laps', [], 5)
    >>> _parseLaps(['laps', '1', '5'])
    ('laps', [1], 5)
    >>> _parseLaps(['laps', '1', '2', '3', '5'])
    ('laps', [1, 2, 3], 5)
    >>> _parseLaps(['laps'])
    ('error',)
    >>> _parseLaps(['laps', 'foo', '5'])
    ('error',)
    >>> _parseLaps(['laps', '0'])
    ('error',)
    >>> _parseLaps(['laps', '-2'])
    ('error',)
    >>> _parseLaps(['laps', 'foo'])
    ('error',)
    '''
    if token[0] != 'laps':
        return None
    if len(token) == 1:
        return _error()
    cids = _parseCategoryIds(token[1:-1])
    if _is_error(cids):
        return cids
    try:
        laps = int(token[-1])
    except ValueError:
        return _error()
    if laps < 1:
        return _error()
    return (LAPS, cids, laps)

def _parseSplit(token):
    '''
    >>> _parseSplit(['1', '12:00:00'])
    ('split', [1], (12, 0, 0))
    >>> _parseSplit(['1', '2', '3', '12:00:00'])
    ('split', [1, 2, 3], (12, 0, 0))
    >>> _parseSplit([])
    ('error',)
    >>> _parseSplit(['foo'])
    ('error',)
    >>> _parseSplit(['1', 'foo'])
    ('error',)
    >>> _parseSplit(['foo', '12:00:00'])
    ('error',)
    '''
    if len(token) < 2:
        return _error()
    bibs = _parseBibs(token[:-1])
    if _is_error(bibs):
        return bibs
    time = _parseTime(token[-1])
    if _is_error(time):
        return time
    return (SPLIT, bibs, time)

def _parseReglist(token):
    '''
    >>> _parseReglist(['foo']) # is None
    >>> _parseReglist(['reglist', './reglist.csv'])
    ('reglist', './reglist.csv')
    >>> _parseReglist(['reglist', './RegList.csv'])
    ('reglist', './RegList.csv')
    >>> _parseReglist(['reglist', '\\'./reg list.csv\\''])
    ('reglist', './reg list.csv')
    >>> _parseReglist(['reglist', '"./reg list.csv"'])
    ('reglist', './reg list.csv')
    >>> _parseReglist(['reglist'])
    ('error',)
    >>> _parseReglist(['reglist', './reglist1.csv', './reglist2.csv'])
    ('error',)
    '''
    if token[0] != 'reglist':
        return None
    if len(token) != 2:
        return _error()
    path = token[1]
    path = path.strip('\'')
    path = path.strip('\"')
    return (REGLIST, path)

def _parseCategoryIds(token):
    '''
    >>> _parseCategoryIds([])
    []
    >>> _parseCategoryIds([1])
    [1]
    >>> _parseCategoryIds([1, 2, 3])
    [1, 2, 3]
    >>> _parseCategoryIds([1, 'foo', 3])
    ('error',)
    >>> _parseCategoryIds([1, 0, 3])
    ('error',)
    >>> _parseCategoryIds([1, -2, 3])
    ('error',)
    '''
    try:
        cids = list(map(int, token))
    except ValueError:
        return _error()
    for cid in cids:
        if cid < 1:
            return _error()
    return cids

import time
def _parseTime(token):
    '''
    >>> _parseTime('')
    ('error',)
    >>> _parseTime('foo')
    ('error',)
    >>> _parseTime('24:00:00')
    ('error',)
    >>> _parseTime('25:00:00')
    ('error',)
    >>> _parseTime('00:00:00')
    (0, 0, 0)
    >>> _parseTime('23:59:59')
    (23, 59, 59)
    >>> _parseTime('13:14:15')
    (13, 14, 15)
    '''
    try:
        tm = time.strptime(token, '%H:%M:%S')
    except ValueError:
        return _error()
    return (tm.tm_hour, tm.tm_min, tm.tm_sec)

def _parseBibs(token):
    '''
    >>> _parseBibs([])
    []
    >>> _parseBibs([0])
    [0]
    >>> _parseBibs([1])
    [1]
    >>> _parseBibs([11])
    [11]
    >>> _parseBibs([1, 2, 3])
    [1, 2, 3]
    >>> _parseBibs([1, 'foo', 3])
    ('error',)
    >>> _parseBibs([1, -2, 3])
    ('error',)
    '''
    try:
        bibs = list(map(int, token))
    except ValueError:
        return _error()
    for bib in bibs:
        if bib < 0:
            return _error()
    return bibs

def _parseItt(token):
    '''
    >>> _parseItt(['itt'])
    ('itt',)
    >>> _parseItt(['itt', 'foo'])
    ('error',)
    >>> _parseItt(['itta']) # is None
    '''
    if token[0] != 'itt':
        return None

    if len(token) != 1:
        return _error()

    return (ITT,)
    
_parsers = [
    _parseStart,
    _parseLaps,
    _parseReglist,
    _parseItt,
    _parseSplit,
    lambda _: _error()
]

def _error():
    return (SYNTAX_ERROR,)

def _is_error(exp):
    return isinstance(exp, tuple) and len(exp) > 0 and exp[0] == SYNTAX_ERROR

