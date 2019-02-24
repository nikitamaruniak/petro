# flake8: noqa

import sys
import os
import csv
import datetime

from jinja2 import Environment, FileSystemLoader

from race import Race, ParticipantState
from reglist import Reglist
import splitfile


def _state_ua_str(state):
    if state == ParticipantState.FINISHED:
        return 'Фінішував'
    elif state == ParticipantState.DNF:
        return 'Зійшов'
    elif state == ParticipantState.RACING:
        return 'На колі'
    elif state == ParticipantState.WARMING_UP:
        return 'Готується'


_error_count = 0


def _error(line_number, message):
    global _error_count
    print('ERROR: Line {}. {}'.format(line_number, message))
    _error_count += 1
    if _error_count == 5:
        sys.exit(2)


if __name__ == '__main__':
    help = 'Use: python -m petro.py <path_to_split_file> <csv|html> <path_to_output_file>'

    if len(sys.argv) != 4:
        print(help)
        sys.exit(1)

    input_path = sys.argv[1]
    output_format = sys.argv[2]
    output_path = sys.argv[3]

    reglist = None
    races = {}

    for expression in splitfile.open_split(input_path):
        try:
            line_number, etype, *params = expression

            if etype == splitfile.expression.SYNTAX_ERROR:
                _error(line_number, 'Syntax error.')
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
                    _error(line_number, 'Duplicate reglist statement.')
            elif etype == splitfile.expression.LAPS:
                if reglist is None:
                    _error(line_number, 'Reglist is not specified.')
                else:
                    category_ids, laps = params
                    for id in category_ids:
                        if id in races:
                            _error(line_number, 'Duplicate laps statement.')
                        elif reglist.participants(id) is None:
                            _error(line_number, 'Category not found.')
                        else:
                            bibs = [p.bib for p in reglist.participants(id) if p.bib is not None]
                            races[id] = Race(laps=laps, bibs=bibs)
            elif etype == splitfile.expression.START:
                if reglist is None:
                    _error(line_number, 'Reglist is not specified.')
                else:
                    category_ids, time_tuple = params
                    for id in category_ids:
                        if id not in races:
                            _error(line_number, 'Category not found or laps are not specified.')
                        elif races[id].started:
                            _error(line_number, 'Duplicate start statement.')
                        else:
                            races[id].start(time_tuple)
            elif etype == splitfile.expression.DNF:
                if reglist is None:
                    _error(line_number, 'Reglist is not specified.')
                else:
                    bibs = params[0]
                    for bib in bibs:
                        participant = reglist.participant(bib)
                        if not participant:
                            _error(line_number, 'Participant not found.')
                        if participant.category_id not in races:
                            _error(line_number, 'Laps are not specified.')
                        else:
                            races[participant.category_id].dnf(participant.bib)
            elif etype == splitfile.expression.SPLIT:
                if reglist is None:
                    _error(line_number, 'Reglist is not specified.')
                else:
                    bibs, time_tuple = params
                    for bib in bibs:
                        participant = reglist.participant(bib)
                        if not participant:
                            _error(line_number, 'Participant not found.')
                        elif participant.category_id not in races:
                            _error(line_number, 'Laps are not specified.')
                        else:
                            races[participant.category_id].split(participant.bib, time_tuple)
        except ValueError as e:
            _error(line_number, repr(e))

    if _error_count > 0:
        sys.exit(2)

    if reglist is None:
        sys.exit(0)

    if output_format == 'csv':
        with open(output_path, mode='wt', encoding='cp1251') as f:
            writer = csv.writer(f, delimiter=';')

            laps = 0
            for race in races.values():
                laps = max(laps, race.laps)
            header = [
                'Место',
                'Номер',
                'Категория',
                'Кол-во человек в команде',
                'userid',
                '',
                'Фамилия',
                'Имя',
                'Ник',
                'Команда',
                'Возраст',
                'Велосипед',
                'Город',
                'Кругов',
                'Штраф',
            ]
            for i in range(1, laps + 1):
                header.append('Круг{}'.format(i))
            writer.writerow(header)

            for category_id, category_name in reglist.categories:
                if category_id not in races:
                    continue
                for result in races[category_id].results:
                    participant = reglist.participant(result.bib)
                    row = [
                        result.position if result.state != ParticipantState.DNF else 'Сход',
                        participant.bib,
                        category_name,
                        '',
                        '',
                        participant.name,
                        '',
                        '',
                        participant.nickname,
                        participant.team,
                        participant.age,
                        '',
                        participant.city,
                        result.laps_done,
                        ''
                    ]
                    row += result.lap_times
                    row += [''] * (laps - result.laps_done)

                    writer.writerow(row)
    else:
        context = {
            'current_time': datetime.datetime.now().strftime('%H:%M:%S'),
            'races': [],
        }

        for category_id, category_name in reglist.categories:
            if category_id not in races:
                continue
            race = races[category_id]
            laps = race.laps
            r = {
                'category_name': category_name,
                'laps': race.laps,
                'start_time': race.start_time if race.started else 'очікується',
                'results': [],
                'riders_on_course': race.riders_on_course
            }

            for result in race.results:
                participant = reglist.participant(result.bib)
                r['results'].append({
                    'state': _state_ua_str(result.state),
                    'position': result.position,
                    'bib': participant.bib,
                    'name': participant.name,
                    'team': participant.team,
                    'city': participant.city,
                    'age': participant.age,
                    'laps_done': result.laps_done,
                    'total_time': result.total_time,
                    'lap_times': result.lap_times
                })
            context['races'].append(r)

        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        tpl = env.get_template('petro.html')
        tpl.stream(context).dump(output_path, encoding='utf-8')
