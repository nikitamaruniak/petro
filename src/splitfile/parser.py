import time

from . import expression


def parse(lines):
    """
    Parses a series of strings

    Supported expressions:
      * <bib> [<bib> ...] <time>
      * start <cid> [<cid> ...] <time>
      * laps <cid> [<cid> ...] <laps> [<time>]
      * reglist <path> [<time>]
      * dnf <bib> [<time>]
    Where:
      * bib - bib number, positive number starting from zero.
      * cid - category id, positive number starting from 1.
      * laps - number of laps, positive number starting from 1.
      * path - absolute or relative path to a bikeportal reglist file, string.
      * time - time of a day, string in the hh:mm:ss format.

    Comments:
      Two consecutive dashes means start of the comment (--). They and
      everything that follows them till the end of a line is ignored.

    Whitespace:
      * Empty lines have no special meaning.
      * Trailing spaces and tabs are ignored.
      * Sequences of spaces or tabs have the same meaning as a one symbol.

    :param lines: iterable of strings.
    :returns: an iterator of expressions presented as tuples
              (line_number, expression, *expression_params).

    >>> list(parse([
    ...     'foo',
    ...     'laps 1 5',
    ...     'start 1 12:13:14',
    ...     '',
    ...     '10 12:35:00',
    ...     'dnf 7 12:36:00'
    ... ]))
    [\
(1, 'error')\
, (2, 'laps', [1], 5)\
, (3, 'start', [1], '12:13:14')\
, (5, 'split', [10], '12:35:00')\
, (6, 'dnf', [7])\
]
    """
    for line_number, line in enumerate(lines):
        e = _parse(line)
        if e:
            yield (line_number + 1,) + e


def _parse(line):
    """
    >>> _parse('') # is None
    >>> _parse('   ') # is None
    >>> _parse('-- some comments on an empty line') # is None
    >>> _parse('foo')
    ('error',)

    >>> _parse('start 1 12:00:00')
    ('start', [1], '12:00:00')
    >>> _parse('start 1 12:00:00\\n')
    ('start', [1], '12:00:00')
    >>> _parse('start 1 2 3 12:00:00')
    ('start', [1, 2, 3], '12:00:00')
    >>> _parse('start')
    ('error',)
    >>> _parse('start 12:00:00')
    ('error',)
    >>> _parse('start foo 12:00:00')
    ('error',)
    >>> _parse('start 1 foo')
    ('error',)

    >>> _parse('laps 1 5')
    ('laps', [1], 5)
    >>> _parse('laps 1 2 3 5')
    ('laps', [1, 2, 3], 5)
    >>> _parse('laps 1 5 12:00:00')
    ('laps', [1], 5)
    >>> _parse('laps')
    ('error',)
    >>> _parse('laps 5')
    ('error',)
    >>> _parse('laps foo 5')
    ('error',)
    >>> _parse('laps 0')
    ('error',)
    >>> _parse('laps -2')
    ('error',)
    >>> _parse('laps foo')
    ('error',)

    >>> _parse('1 12:00:00')
    ('split', [1], '12:00:00')
    >>> _parse('1 2 3 12:00:00')
    ('split', [1, 2, 3], '12:00:00')

    >>> _parse('foo')
    ('error',)
    >>> _parse('1 foo')
    ('error',)
    >>> _parse('foo 12:00:00')
    ('error',)
    >>> _parse('foo 1 12:00:00')
    ('error',)

    >>> _parse('reglist ./reglist.csv')
    ('reglist', './reglist.csv')
    >>> _parse('reglist ./RegList.csv')
    ('reglist', './RegList.csv')
    >>> _parse('reglist \\'./reg list.csv\\'')
    ('reglist', './reg list.csv')
    >>> _parse('reglist "./reg list.csv"')
    ('reglist', './reg list.csv')
    >>> _parse('reglist "./reg list.csv" 12:00:00')
    ('reglist', './reg list.csv')
    >>> _parse('reglist')
    ('error',)
    >>> _parse('reglist ./reglist1.csv ./reglist2.csv')
    ('error',)

    >>> _parse('dnf 1')
    ('dnf', [1])
    >>> _parse('dnf 1 2')
    ('dnf', [1, 2])
    >>> _parse('dnf 1 2 12:00:00')
    ('dnf', [1, 2])
    >>> _parse('dnf')
    ('error',)
    >>> _parse('dnf foo 12:00:00')
    ('error',)
    >>> _parse('dnf 1 foo')
    ('error',)
    """
    t = _token(line)
    if not t:
        return None
    if not _is_error(t):
        e = _expression(t)
    else:
        e = t
    return e


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
    >>> _token('foo -2')
    ['foo', '-2']
    >>> _token('foo 2- 3')
    ['foo', '2-', '3']
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

        if c != '-' and comment_start != -1:
            if token_start == -1:
                token_start = comment_start
            comment_start = -1

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


def _parse_laps(token):
    if token[0] != 'laps':
        return None
    if len(token) == 1:
        return _error()
    if not _is_error(_parse_time(token[-1])):
        token = token[:-1]
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
    if token[0] != 'reglist':
        return None
    if not _is_error(_parse_time(token[-1])):
        token = token[:-1]
    if len(token) != 2:
        return _error()
    path = token[1]
    path = path.strip('\'')
    path = path.strip('\"')
    return expression.REGLIST, path


def _parse_category_ids(token):
    """
    >>> _parse_category_ids([])
    ('error',)
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
    if not token:
        return _error()
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
    '00:00:00'
    >>> _parse_time('23:59:59')
    '23:59:59'
    >>> _parse_time('13:14:15')
    '13:14:15'
    """
    try:
        time.strptime(token, '%H:%M:%S')
    except ValueError:
        return _error()
    return token


def _parse_bibs(token):
    """
    >>> _parse_bibs([])
    ('error',)
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
    if not bibs:
        return _error()
    for bib in bibs:
        if bib < 0:
            return _error()
    return bibs


def _parse_dnf(token):
    if token[0] != 'dnf':
        return None
    if not _is_error(_parse_time(token[-1])):
        token = token[:-1]
    bibs = _parse_bibs(token[1:])
    if _is_error(bibs):
        return bibs
    return expression.DNF, bibs


_parsers = [
    _parse_start,
    _parse_laps,
    _parse_reglist,
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
