from parsley import makeGrammar
import ometa

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
    >>> _parse('banner')
    ('error',)
    >>> _parse('banner foo baz bar')
    ('error',)
    >>> _parse('banner foo.png')
    ('banner', 'foo.png')
    >>> _parse('banner "foo baz bar.png"')
    ('banner', 'foo baz bar.png')
    >>> _parse("banner 'foo baz bar.png'")
    ('banner', 'foo baz bar.png')
    """
    try:
        return _parser(line).specification()
    except ometa.runtime.ParseError:
        return (expression.SYNTAX_ERROR,)


_specification = """
ws = ' ' | '\t' | '\n'
space = ws+
optional_space = ws*

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

optional_timestamp = (space time)?

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

char = ~ws ~single_quote ~double_quote anything

string =
      (single_quote <(char | space)*>:s single_quote) -> s
    | (double_quote <(char | space)*>:s double_quote) -> s
    | <char*>:s -> s

reglist =
    'reglist'
    space string:filepath
    optional_timestamp -> Reglist(filepath)

banner =
    'banner'
    space string:url
    optional_timestamp -> Banner(url)

comment = '--' anything*

statement = reglist | banner | laps | start | split | dnf

specification =
    optional_space statement?:stmt optional_space comment? -> stmt
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
    'Banner':
        lambda url: (expression.BANNER, url)
}

_parser = makeGrammar(_specification, _factories)
