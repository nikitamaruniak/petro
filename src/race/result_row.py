from collections.__init__ import namedtuple

ResultRow = namedtuple(
    'ResultRow',
    ['position', 'state', 'bib', 'laps_done', 'total_time', 'lap_times']
)
