from parser import *

__all__ = ['SplitFile']

class SplitFile(object):
    def __init__(self, expressions):
       self._expressions = expressions

    @classmethod
    def open(cls, file_path):
        expressions = list(parse(_file_iter(file_path)))
        return cls(expressions)

    def __iter__(self):
        return (e for e in self._expressions)
        
def _file_iter(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line
