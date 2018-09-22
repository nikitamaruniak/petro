import csv

from .participant import Participant


class Reglist:
    def __init__(self, categories, participants):
        self._bibs = {}
        self._categories = {}
        for cid, cname in categories:
            self._categories[cid] = (cname, [])

        for p in participants:
            __, ps = self._categories[p.category_id]
            ps.append(p)
            if p.bib is not None:
                self._bibs[p.bib] = p

    @property
    def categories(self):
        for cid in self._categories.keys():
            cname, __ = self._categories[cid]
            yield (cid, cname)

    def participants(self, category_id):
        if category_id in self._categories:
            __, ps = self._categories[category_id]
            return (p for p in ps)
        else:
            return None

    def participant(self, bib):
        if bib in self._bibs:
            return self._bibs[bib]
        else:
            return None

    @staticmethod
    def open(file_path):
        participants = []
        categories = []
        category_id = None
        for row in _csv_lines(file_path):
            if row[0] != '' and row[1] == '':
                category_name = row[0]
                category_id = category_id + 1 if category_id else 1
                categories.append((category_id, category_name))
            elif category_id is not None:
                # Номер;Имя;Ник;Команда;Откуда;Возраст;*
                bib, name, nickname, team, city, age, *_ = row
                p = Participant(
                    bib=bib if len(bib) else None,
                    category_id=category_id,
                    name=name,
                    nickname=nickname,
                    team=team,
                    city=city,
                    age=age)
                participants.append(p)
        return Reglist(categories, participants)


def _csv_lines(file_path):
    with open(file_path, mode='rt', encoding='cp1251') as f:
        reader = csv.reader(
            f,
            delimiter=';',
            lineterminator='\r\n',
            strict=True)

        for row in reader:
            yield row
