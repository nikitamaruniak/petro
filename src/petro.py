import sys
import os

from csv_writer import write as write_csv
from html_writer import write as write_html
from race import Race
from reglist import Reglist
import splitfile


def _main(argv):
    global _error_count
    _error_count = 0
    help = 'Use: python -m petro.py <path_to_split_file> <csv|html> <path_to_output_file>'

    if len(argv) != 4:
        print(help)
        return 1

    input_path = argv[1]
    output_format = argv[2]
    output_path = argv[3]

    class TooManyErrors(Exception):
        pass

    def on_error(line_number, message):
        global _error_count
        print('ERROR: Line {}. {}'.format(line_number, message))
        _error_count += 1
        if _error_count == 5:
            raise TooManyErrors()

    try:
        races, reglist = _results(input_path, on_error=on_error)
    except TooManyErrors:
        return 2

    if _error_count > 0:
        return 2

    if reglist is None:
        return 0

    writers = {
        'csv': write_csv,
        'html': write_html
    }

    writers[output_format](output_path, races, reglist)


def _results(input_path, on_error):
    reglist = None
    races = {}
    for expression in splitfile.open_split(input_path):
        line_number, etype, *params = expression

        if etype == splitfile.expression.SYNTAX_ERROR:
            on_error(line_number, 'Syntax error.')
        elif etype == splitfile.expression.REGLIST:
            path = params[0]
            if not os.path.isabs(path):
                path = os.path.abspath(
                    os.path.join(
                        os.path.abspath(
                            os.path.dirname(input_path)),
                        path))
            if reglist is None:
                reglist = Reglist.open(path)
            else:
                on_error(line_number, 'Duplicate reglist statement.')
        elif etype == splitfile.expression.LAPS:
            if reglist is None:
                on_error(line_number, 'Reglist is not specified.')
            else:
                category_ids, laps = params
                for id in category_ids:
                    if id in races:
                        on_error(line_number, 'Duplicate laps statement.')
                    elif reglist.participants(id) is None:
                        on_error(line_number, 'Category not found.')
                    else:
                        bibs = [p.bib for p in reglist.participants(id) if p.bib is not None]
                        races[id] = Race(laps=laps, bibs=bibs)
        elif etype == splitfile.expression.START:
            if reglist is None:
                on_error(line_number, 'Reglist is not specified.')
            else:
                category_ids, time_tuple = params
                for id in category_ids:
                    if id not in races:
                        on_error(line_number, 'Category not found or laps are not specified.')
                    elif races[id].started:
                        on_error(line_number, 'Duplicate start statement.')
                    else:
                        races[id].start(time_tuple)
        elif etype == splitfile.expression.DNF:
            if reglist is None:
                on_error(line_number, 'Reglist is not specified.')
            else:
                bibs = params[0]
                for bib in bibs:
                    participant = reglist.participant(bib)
                    if not participant:
                        on_error(line_number, 'Participant not found.')
                    if participant.category_id not in races:
                        on_error(line_number, 'Laps are not specified.')
                    else:
                        races[participant.category_id].dnf(participant.bib)
        elif etype == splitfile.expression.SPLIT:
            if reglist is None:
                on_error(line_number, 'Reglist is not specified.')
            else:
                bibs, time_tuple = params
                for bib in bibs:
                    participant = reglist.participant(bib)
                    if not participant:
                        on_error(line_number, 'Participant not found.')
                    elif participant.category_id not in races:
                        on_error(line_number, 'Laps are not specified.')
                    else:
                        races[participant.category_id].split(participant.bib, time_tuple)

    return races, reglist


if __name__ == '__main__':
    sys.exit(_main(sys.argv))
