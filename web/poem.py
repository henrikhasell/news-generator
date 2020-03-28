import datetime
import logging
import markovify
import storage
import uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta


def generate_poem_uuid():
    return f'{uuid.uuid4()}'[:8]


class Poem:
    def __init__(self, paragraphs, date_generated, mode, uuid=None):
        self.paragraphs = paragraphs
        self.date_generated = date_generated
        self.mode = mode
        if not uuid:
            self.save()

    def save(self):
        self.uuid = generate_poem_uuid()
        storage.save_poem(self)


class PoemGenerator:
    def __init__(self):
        logging.debug("PoemGenerator init START")
        now = datetime.now()
        self.combined_files = self._get_text(datetime(1970, 1, 1), now)
        self.combined_this_year = self._get_text(now - relativedelta(years=1), now)
        self.combined_this_month = self._get_text(now - relativedelta(months=1), now)
        self.combined_today = self._get_text(now - relativedelta(days=1), now)
        logging.debug("PoemGenerator init END")

    def _get_this_year_text(self):
        now = datetime.now()
        return self._get_text(now - relativedelta(years=1), now)

    def _get_this_month_text(self):
        now = datetime.now()
        return self._get_text(now - relativedelta(months=1), now)

    def _get_this_days_text(self):
        now = datetime.now()
        return self._get_text(now - relativedelta(days=1), now)

    def generate_poem(self, mode='all'):
        logging.debug("Poem generation start.")

        markov_dict = {
            'all': self.combined_files,
            'this_month': self.combined_this_month,
            'this_year': self.combined_this_year,
            'today': self.combined_today
        }

        chosen_dict = markov_dict[mode]
        logging.debug("Markov dictionary picked.")

        result = []

        for i in range(4):
            result += [chosen_dict.make_short_sentence(150)]
            logging.debug(f"Generated short sentence {i + 1} of 4.")

        paragraphs = list(i for i in result if i != None)
        return Poem(paragraphs, datetime.now(), mode)

    def _get_text(self, from_date, until_date):
        text = storage.get_text(from_date, until_date)
        try:
            result = markovify.Text(text)
        except KeyError as e:
            result = self.combined_files if hasattr(self, 'combined_files') else ''
        return result
