import doctest

import splitfile.parser


# noinspection PyUnusedLocal
def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(splitfile.parser))
    return tests
