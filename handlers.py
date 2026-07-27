from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.age_calc import DateParseError, calculate_age, format_result, parse_date

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "*AgeFinderBot*\n\n"
    "Send me a date of birth in pretty much any format — `1995-08-21`, "
    "`21/08/1995`, `August 21, 1995` — and I'll work out the exact age, "
    "zodiac signs, and days until the next birthday.\n\n"
    "Commands:\n"
    "/age <date> - same as just sending the date directly\n"
    "/recalc - re-show the result for the last date you sent\n"
    "/help - show this message"
)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to AgeFinderBot!\n\n" + HELP_TEXT, parse_mode="Markdown"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def _handle_date_text(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_text: str):
    try:
        birth_date = parse_date(raw_text)
        result = calculate_age(birth_date)
    except DateParseError as exc:
        await update.message.reply_text(str(exc))
        return

    context.user_data["last_birth_date"] = birth_date.isoformat()
    await update.message.reply_text(format_result(result), parse_mode="Markdown")


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_date_text(update, context, update.message.text)


async def age_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = " ".join(context.args)
    if not raw:
        await update.message.reply_text(
            "Usage: `/age 1995-08-21` (or just send the date on its own)", parse_mode="Markdown"
        )
        return
    await _handle_date_text(update, context, raw)


async def recalc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last = context.user_data.get("last_birth_date")
    if not last:
        await update.message.reply_text("Send me a date of birth first, then I can recalculate it.")
        return
    await _handle_date_text(update, context, last)
