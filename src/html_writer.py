import datetime
import os

from jinja2 import Environment, FileSystemLoader

from race import ParticipantState


def write(output_path, races, reglist, banner_url):
    context = {
        'banner_url': banner_url,
        'current_time': datetime.datetime.now().strftime('%H:%M:%S'),
        'races': [],
    }
    for category_id, category_name in reglist.categories:
        if category_id not in races:
            continue
        race = races[category_id]
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


def _state_ua_str(state):
    if state == ParticipantState.FINISHED:
        return 'Фінішував'
    elif state == ParticipantState.DNF:
        return 'Зійшов'
    elif state == ParticipantState.RACING:
        return 'На колі'
    elif state == ParticipantState.WARMING_UP:
        return 'Готується'
