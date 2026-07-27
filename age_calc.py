from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

_WEEKDAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]

_WESTERN_ZODIAC = [
    (1, 20, "Capricorn"), (2, 19, "Aquarius"), (3, 20, "Pisces"),
    (4, 20, "Aries"), (5, 21, "Taurus"), (6, 21, "Gemini"),
    (7, 22, "Cancer"), (8, 23, "Leo"), (9, 23, "Virgo"),
    (10, 23, "Libra"), (11, 22, "Scorpio"), (12, 21, "Sagittarius"),
    (12, 31, "Capricorn"),
]

_CHINESE_ZODIAC = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
]


class DateParseError(ValueError):
    pass


@dataclass
class AgeResult:
    birth_date: date
    years: int
    months: int
    days: int
    total_days_lived: int
    total_weeks_lived: int
    weekday_born: str
    western_zodiac: str
    chinese_zodiac: str
    next_birthday: date
    days_until_next_birthday: int
    next_birthday_weekday: str


def parse_date(text: str) -> date:
    """Parses a wide range of human-entered date formats. Raises DateParseError
    if the text can't be understood or if it isn't a real, past-or-today date.
    """
    text = text.strip()
    if not text:
        raise DateParseError("Please send a date of birth, e.g. 1995-08-21 or 21 August 1995.")

    try:
        # dayfirst=False first (handles ISO and US-style MM/DD/YYYY);
        # if that yields an obviously wrong future date we retry dayfirst.
        parsed = date_parser.parse(text, fuzzy=True, default=datetime(1, 1, 1))
    except (ValueError, OverflowError):
        raise DateParseError(
            "I couldn't understand that date. Try formats like `1995-08-21`, `21/08/1995`, or `August 21 1995`."
        )

    result = parsed.date()

    if result > date.today():
        # Try the day-first interpretation in case it was e.g. "08/21/1995"
        # misread, or genuinely just an invalid future date.
        try:
            alt = date_parser.parse(text, fuzzy=True, dayfirst=True, default=datetime(1, 1, 1)).date()
            if alt <= date.today():
                result = alt
        except (ValueError, OverflowError):
            pass

    if result > date.today():
        raise DateParseError("That date is in the future — please send an actual date of birth.")

    if result.year < 1900:
        raise DateParseError("That year looks off — please double check the date.")

    return result


def _western_zodiac(month: int, day: int) -> str:
    for cutoff_month, cutoff_day, sign in _WESTERN_ZODIAC:
        if (month, day) <= (cutoff_month, cutoff_day):
            return sign
    return "Capricorn"


def _chinese_zodiac(year: int) -> str:
    return _CHINESE_ZODIAC[(year - 4) % 12]


def calculate_age(birth_date: date, today: date | None = None) -> AgeResult:
    today = today or date.today()
    if birth_date > today:
        raise DateParseError("That date is in the future — please send an actual date of birth.")

    delta = relativedelta(today, birth_date)
    total_days = (today - birth_date).days

    next_bday = birth_date.replace(year=today.year)
    if next_bday < today:
        next_bday = next_bday.replace(year=today.year + 1)
    elif next_bday == today:
        next_bday = today
    days_until = (next_bday - today).days

    return AgeResult(
        birth_date=birth_date,
        years=delta.years,
        months=delta.months,
        days=delta.days,
        total_days_lived=total_days,
        total_weeks_lived=total_days // 7,
        weekday_born=_WEEKDAYS[birth_date.weekday()],
        western_zodiac=_western_zodiac(birth_date.month, birth_date.day),
        chinese_zodiac=_chinese_zodiac(birth_date.year),
        next_birthday=next_bday,
        days_until_next_birthday=days_until,
        next_birthday_weekday=_WEEKDAYS[next_bday.weekday()],
    )


def format_result(result: AgeResult) -> str:
    bday_note = "🎉 Today is the birthday!" if result.days_until_next_birthday == 0 else (
        f"{result.days_until_next_birthday} days until the next birthday "
        f"({result.next_birthday.isoformat()}, a {result.next_birthday_weekday})"
    )

    return (
        "*Age Finder*\n\n"
        f"Date of birth: *{result.birth_date.isoformat()}* ({result.weekday_born})\n\n"
        f"Exact age: *{result.years} years, {result.months} months, {result.days} days*\n"
        f"Total days lived: *{result.total_days_lived:,}*\n"
        f"Total weeks lived: *{result.total_weeks_lived:,}*\n\n"
        f"Western zodiac: *{result.western_zodiac}*\n"
        f"Chinese zodiac: *{result.chinese_zodiac}*\n\n"
        f"{bday_note}"
    )
