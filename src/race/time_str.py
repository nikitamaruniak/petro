from datetime import datetime

from .errors import MalformedTimeString


def time_str_to_datetime(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M:%S')
    except ValueError:
        raise MalformedTimeString()


def timedelta_to_time_str(td):
    if td.days < 0:
        raise NotImplemented('Negative timedelta values are not supported.')
    return '{:02}:{:02}:{:02}'.format(
        td.days * 24 + td.seconds // 3600,
        (td.seconds % 3600) // 60,
        (td.seconds % 3600) % 60)
