class Participant:
    def __init__(self, bib, name, category_id):
        self._bib = bib if bib != '' else None
        self._name = name
        self._category_id = category_id

    @property
    def bib(self):
        return self._bib

    @property
    def name(self):
        return self._name

    @property
    def category_id(self):
        return self._category_id
