# flake8: noqa

import sys
import os
import csv
import datetime

from race import Race, ParticipantState
from reglist import Reglist
import splitfile


def _time_str(time_tuple):
    return '{:02}:{:02}:{:02}'.format(
        time_tuple[0],
        time_tuple[1],
        time_tuple[2])


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
                            races[id].start(_time_str(time_tuple))
            elif etype == splitfile.expression.DNF:
                if reglist is None:
                    _error(line_number, 'Reglist is not specified.')
                else:
                    bibs, _ = params
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
                    time_str = _time_str(time_tuple)
                    for bib in bibs:
                        participant = reglist.participant(bib)
                        if not participant:
                            _error(line_number, 'Participant not found.')
                        elif participant.category_id not in races:
                            _error(line_number, 'Laps are not specified.')
                        else:
                            races[participant.category_id].split(participant.bib, time_str)
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
                position = 1
                for result in races[category_id].results:
                    participant = reglist.participant(result.bib)
                    row = [
                        position if result.state != ParticipantState.DNF else 'Сход',
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
                    position += 1

                    writer.writerow(row)
    else:
        html = []
        html.append('<!DOCTYPE html>')
        html.append('<html lang="uk-UA">')
        html.append('<head>')
        html.append('   <meta charset="UTF-8">')
        html.append('   <title>Результати</title>')
        html.append('''   <style>'
        tbody tr:nth-child(odd) {
            background-color: #ffffff;
        }
    
        tbody tr:nth-child(even) {
            background-color: #e8edff;
        }

        table {
            border-collapse: collapse;
            font-family: Sans-Serif;
            font-size: 12px;
        }

        td, th {
            border-bottom: 1px solid #ddd;
            padding: 0.3rem;
            text-align: left;
        }
        </style>''')
        html.append('</head>')
        html.append('<body>')
        current_time_str = datetime.datetime.now().strftime('%H:%M:%S')
        html.append('   <img src=\'banner.png\'/>')
        html.append('   <p>Час створення протоколу: {}</p>'.format(current_time_str))
        for category_id, category_name in reglist.categories:
            if category_id not in races:
                continue
            race = races[category_id]
            laps = race.laps
            html.append('   <h1>{}</h1>'.format(category_name))
            start_time_str = race.start_time if race.started else 'очікується'
            html.append('   <p>Час старту категорії: {}</p>'.format(start_time_str))

            html.append('   <table>')

            html.append('   <tr>')
            html.append('       <th>{}</th>'.format('Статус'))
            html.append('       <th>{}</th>'.format('Поз.'))
            html.append('       <th>{}</th>'.format('Номер'))
            html.append('       <th>{}</th>'.format('ПІБ'))
            html.append('       <th>{}</th>'.format('Команда'))
            html.append('       <th>{}</th>'.format('Місто'))
            html.append('       <th>{}</th>'.format('Вік'))
            html.append('       <th>{}</th>'.format('К. кіл'))
            html.append('       <th>{}</th>'.format('Заг. час'))
            for i in range(1, laps + 1):
                html.append('       <th>{}{}</th>'.format('Коло ', i))
            html.append('   </tr>')

            position = 1
            for result in race.results:
                participant = reglist.participant(result.bib)
                state_str = _state_ua_str(result.state)
                html.append('   <tr>')
                html.append('       <td>{}</td>'.format(state_str))
                html.append('       <td>{}</td>'.format(str(position)))
                html.append('       <td>{}</td>'.format(participant.bib))
                html.append('       <td>{}</td>'.format(participant.name))
                html.append('       <td>{}</td>'.format(participant.team))
                html.append('       <td>{}</td>'.format(participant.city))
                html.append('       <td>{}</td>'.format(participant.age))
                html.append('       <td>{}</td>'.format(result.laps_done))
                html.append('       <td>{}</td>'.format(result.total_time))
                for lap_time in result.lap_times:
                    html.append('       <td>{}</td>'.format(lap_time))
                for _ in range(laps - result.laps_done):
                    html.append('       <td></td>')
                html.append('   </tr>')
                position += 1
            html.append('   </table>')
        html.append('</body>')
        html.append('</html>')

        with open(output_path, mode='w', encoding='utf-8') as f:
            for line_number in html:
                f.write(line_number)
                f.write('\n')
