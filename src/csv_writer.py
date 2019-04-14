import csv

from race import ParticipantState


def write(output_path, races, reglist, banner_url):
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
