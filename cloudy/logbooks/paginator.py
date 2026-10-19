import json

from django.conf import settings
from redis import Redis

from cloudy.core.utils import decode_datetime, encode_datetime

# I'm not sure this is really thread-safe.
REDIS = Redis(
    host=settings.REDIS_SERVER,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
)


def clear_cache(logbook):
    """
    Clear the pagination cache for the given logbook
    """
    REDIS.delete("paging:%s" % logbook.id)


def logs_for_page(logbook, page, maxrows=14):
    """
    Return (number_of_pages, logs_for_current_page)
    """
    page_date_range = None
    pages_count = 0
    res = None
    logs = logbook.logs_qs()

    if settings.CACHING:
        cached = REDIS.get("paging:%s" % logbook.id)
        if cached is not None:
            pages = json.loads(cached)
            pages_count = len(pages)
            if page == -1:
                page = pages_count
            page_date_range_strings = pages[page - 1]
            page_date_range = map(decode_datetime, page_date_range_strings)

    # If nothing was found in Redis or if we don't have cache
    if page_date_range is None:
        logs = logbook.logs_qs()
        # Guardian no logs at all
        if not logs:
            return 0, []
        res = [[]]
        cursor = 0
        current_year = None
        current_stack_len = 0
        for log in logs:
            if (not log.date.year == current_year) and current_year is not None:
                res.append([log])
                cursor += 1
                current_year = log.date.year
                current_stack_len = 1
            else:
                if current_stack_len == maxrows:
                    res.append([log])
                    current_stack_len = 1
                    cursor += 1
                else:
                    res[cursor].append(log)
                    current_stack_len += 1
                    current_year = log.date.year

        # Let's save the results in Redis
        if settings.CACHING:
            pages_stock = []
            for page_list in res:
                datetime_range = [page_list[0].date, page_list[-1].date]
                string_list = map(encode_datetime, datetime_range)
                pages_stock.append(string_list)
            jsonified = json.dumps(pages_stock)
            REDIS.set("paging:%s" % logbook.id, jsonified)

        # Set the pages count
        pages_count = len(res)

        if page == -1:
            page = pages_count

        # Set the date range for the current query
        page_date_range = [res[page - 1][0].date, res[page - 1][-1].date]

    # We got the timeslice through redis, so we have to grab the logs from
    # mongo
    if res is None:
        return pages_count, list(logbook.logs_qs(tuple(page_date_range)))
    # If we computed the paging, we reuse the results
    else:
        return pages_count, list(res[page - 1])
