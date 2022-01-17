from datetime import date, datetime, timedelta
from fad.utils import record_main_dimensioni


def fix_dimension():
    start_date = date(2020, 10, 15)
    while start_date < date.today():
        print(start_date)
        record_main_dimensioni(start_date.strftime('%Y-%m-%d'))
        start_date += timedelta(days=1)
