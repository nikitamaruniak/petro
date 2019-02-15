from parsley import makeGrammar
import ometa

from . import expression


def parse(lines):
    """
    Converts an iterator of strings into an iterator of expressions.

    Syntax:
        Supported expressions:
        <bib> [<bib> ... <bib>] <time>
        start [<cid> ... <cid>] <time>
        laps [<cid> ... <cid>] <laps>
        reglist <path>
        dnf <bib> <time>

        bib - bib number - positive number starting from zero.
        cid - category id - positive number starting from 1.
        laps - number of laps - positive number starting from 1.
        path - absolute or relative path to the bikeportal reglist file - string.
        time - time of a day - time representation as a string in the hh:mm:ss format.

        Comments:
        Two consecutive dashes mean start of the comment (--). They and
        everything that follows them till the end of line is ignored.

        Whitespace:
        * Empty lines have no special meaning.
        * Trailing spaces and tabs are ignored.
        * Sequences of spaces or tabs have the same meaning as a one symbol.
    # noqa 501
    >>> list(parse(['foo', 'laps 1 5', 'start 1 12:13:14', '', '10 12:35:00', 'dnf 7 12:36:00']))
    [(1, 'error'), (2, 'laps', [1], 5), (3, 'start', [1], '12:13:14'), (5, 'split', [10], '12:35:00'), (6, 'dnf', [7])]
    >>> list(parse([]))
    []
    >>> list(parse(['foo']))
    [(1, 'error')]
    >>> list(parse(['start 1 12:00:00']))
    [(1, 'start', [1], '12:00:00')]
    >>> list(parse(['start 1 12:00:00\\n']))
    [(1, 'start', [1], '12:00:00')]
    >>> list(parse(['start 1 2 3 12:00:00']))
    [(1, 'start', [1, 2, 3], '12:00:00')]
    >>> list(parse(['start']))
    [(1, 'error')]
    >>> list(parse(['start 12:00:00']))
    [(1, 'error')]
    >>> list(parse(['start foo 12:00:00']))
    [(1, 'error')]
    >>> list(parse(['start 1 foo']))
    [(1, 'error')]
    >>> list(parse(['laps 1 5']))
    [(1, 'laps', [1], 5)]
    >>> list(parse(['laps 1 2 3 5']))
    [(1, 'laps', [1, 2, 3], 5)]
    >>> list(parse(['laps']))
    [(1, 'error')]
    >>> list(parse(['laps 5']))
    [(1, 'error')]
    >>> list(parse(['laps foo 5']))
    [(1, 'error')]
    >>> list(parse(['laps 0']))
    [(1, 'error')]
    >>> list(parse(['laps -2']))
    [(1, 'error')]
    >>> list(parse(['laps foo']))
    [(1, 'error')]
    >>> list(parse(['1 12:00:00']))
    [(1, 'split', [1], '12:00:00')]
    >>> list(parse(['1 2 3 12:00:00']))
    [(1, 'split', [1, 2, 3], '12:00:00')]
    >>> list(parse(['foo']))
    [(1, 'error')]
    >>> list(parse(['1 foo']))
    [(1, 'error')]
    >>> list(parse(['foo 12:00:00']))
    [(1, 'error')]
    >>> list(parse(['reglist ./reglist.csv']))
    [(1, 'reglist', './reglist.csv')]
    >>> list(parse(['reglist ./RegList.csv']))
    [(1, 'reglist', './RegList.csv')]
    >>> list(parse(['reglist \\'./reg list.csv\\'']))
    [(1, 'reglist', './reg list.csv')]
    >>> list(parse(['reglist "./reg list.csv"']))
    [(1, 'reglist', './reg list.csv')]
    >>> list(parse(['reglist']))
    [(1, 'error')]
    >>> list(parse(['reglist ./reglist1.csv ./reglist2.csv']))
    [(1, 'error')]
    >>> list(parse(['dnf 1']))
    [(1, 'dnf', [1])]
    >>> list(parse(['dnf 1 2']))
    [(1, 'dnf', [1, 2])]
    >>> list(parse(['foo 1 12:00:00']))
    [(1, 'error')]
    >>> list(parse(['dnf']))
    [(1, 'error')]
    >>> list(parse(['dnf foo 12:00:00']))
    [(1, 'error')]
    >>> list(parse(['dnf 1 foo']))
    [(1, 'error')]
    """
    line_number = 1
    for line in lines:
        try:
            r = _parser(line).specification()
        except ometa.runtime.ParseError as e:
            r = (expression.SYNTAX_ERROR,)
        if r:
            yield (line_number,) + r
        line_number += 1


_specification = """
ws = ' ' | '\t'
space = ws+
optional_space = ws*
newline = '\n'

zero = '0'
digit = anything:x ?(x in '0123456789') -> x
digit1_9 = anything:x ?(x in '123456789') -> x

hours = <digit{2}>:x ?(int(x) < 24) -> x
minutes = <digit{2}>:x ?(int(x) < 60) -> x
seconds = minutes

time = <hours ':' minutes ':' seconds>

positive_number = <~time digit1_9 digit*>:x -> int(x)
natural_number = (~time positive_number | zero):x -> int(x)

bib = natural_number
bibs = bib:first (space bib)*:rest -> [first] + rest

split = bibs:bibs space time:time -> Split(bibs, time)

optional_timestamp = (space time:time)?

dnf = 'dnf' space bibs:bibs optional_timestamp -> Dnf(bibs)

number_of_laps = positive_number
category = number_of_laps

categories = category:first (space category)*:rest -> [first] + rest

start =
    'start'
    space categories:categories
    space time:time -> Start(categories, time)

laps =
    'laps'
    space category:first
    (space category | number_of_laps)+:rest
    optional_timestamp -> Laps([first] + rest[:-1], rest[-1])

single_quote = '\\\''
double_quote = '"'

char = ~newline ~ws ~single_quote ~double_quote anything

string =
      (single_quote <(char | space)*>:s single_quote) -> s
    | (double_quote <(char | space)*>:s double_quote) -> s
    | <char*>:s -> s

reglist =
    'reglist'
    space string:filepath
    optional_timestamp -> Reglist(filepath)

comment = <'--' (~newline anything)*>

statement = reglist | laps | start | split | dnf

specification =
    optional_space
    statement?:stmt
    optional_space comment?
    newline* -> stmt
"""

_factories = {
    'Split':
        lambda bibs, ts: (expression.SPLIT, bibs, ts),
    'Dnf':
        lambda bibs: (expression.DNF, bibs),
    'Start':
        lambda categories, ts: (expression.START, categories, ts),
    'Laps':
        lambda categories, num_laps: (expression.LAPS, categories, num_laps),
    'Reglist':
        lambda filepath: (expression.REGLIST, filepath),
}

_parser = makeGrammar(_specification, _factories)
