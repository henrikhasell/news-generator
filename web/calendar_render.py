import storage
from calendar import monthrange
from datetime import datetime


def chunks(_list, n):
    for i in range(0, len(_list), n):
        yield _list[i:i + n]


def table_json(data_set, year, month):
    result = []

    from_date = datetime(year, month, 1)
    until_date = datetime(year, month, monthrange(year, month)[1])

    for _ in range(from_date.weekday()):
        result += [None]

    for date in data_set:
        result += [{"colour": "#ffffff", "count": data_set[date], "date": date}]

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
