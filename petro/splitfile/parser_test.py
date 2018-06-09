import unittest
import doctest

from . import parser

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(parser))
    return tests

