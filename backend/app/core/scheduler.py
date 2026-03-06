from datetime import date


def is_week_start(day: date) -> bool:
    return day.weekday() == 0

