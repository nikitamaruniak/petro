from collections.__init__ import namedtuple

ResultRow = namedtuple(
    'ResultRow',
    ['state', 'bib', 'laps_done', 'total_time', 'lap_times']
)
