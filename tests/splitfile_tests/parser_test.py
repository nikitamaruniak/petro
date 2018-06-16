import unittest
import doctest

import splitfile.parser

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(splitfile.parser))
    return tests

