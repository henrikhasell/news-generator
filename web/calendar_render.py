import flask
import logging
import storage
from calendar import monthrange
from datetime import datetime


colour_palette = [
    '#edf8e9',
    '#c8e8c2',
    '#a0d69b',
    '#74c476',
    '#41ab5d',
    '#238b45',
    '#005a32',
]


def date_to_link(date):
    year, month, day = map(int, date.split('-'))
    return flask.url_for(
        "calendar_month",
        year=year, month=month, day=day
    )


def chunks(_list, n):
    for i in range(0, len(_list), n):
        yield _list[i:i + n]


def get_style(max_ticks, curr_ticks):
    index = round(curr_ticks / max_ticks * (len(colour_palette) - 1)) if curr_ticks else 0
    logging.debug(f'{max_ticks}/{curr_ticks} = {index}')
    return {
        'cell': f'background-color:{colour_palette[index]}',
        'text': f'color:{"#000" if index < 3 else "#fff"}'
    }


def table_json(data_set, year, month):
    result = []

    from_date = datetime(year, month, 1)
    until_date = datetime(year, month, monthrange(year, month)[1])

    max_ticks = max([i for _, i in data_set.items()], default=0)

    for _ in range(from_date.weekday()):
        result += [None]

    for date in data_set:
        curr_ticks = data_set[date]

        result += [{
            "colour": "#ffffff",
            "count": curr_ticks,
            "date": date,
            "link": date_to_link(date),
            "style": get_style(max_ticks, curr_ticks)
        }]

    for _ in range(until_date.weekday(), 6):
        result += [None]

    return list(chunks(result, 7))


def articles_published_calendar(year, month):
    from_date = datetime(year, month, 1)
    until_date = datetime(year, month, monthrange(year, month)[1])

    article_count = storage.count_articles_by_date_published(
        from_date, until_date)

    return table_json(article_count, year, month)


def articles_published_by_year(year):
    for month in range(1, 13):
        yield {
            'month': datetime(year, month, 1).strftime('%B %Y'),
            'table': articles_published_calendar(year, month)
        }
