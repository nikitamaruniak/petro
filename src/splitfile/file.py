from .parser import parse


def open(file_path, encoding='utf-8'):
    return parse(_file_iter(file_path, encoding))


def _file_iter(file_path, encoding='utf-8'):
    with open(file_path, mode='rt', encoding=encoding) as f:
        for line in f:
            yield line
