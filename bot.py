import os
import re
import logging
import sqlite3

import tle_user as User

from datetime import date, datetime

from threading import Thread
from dotenv import load_dotenv

from telegram.ext import (
    Updater,
    Filters,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
)

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, ChatAction

from tle_user import tle_user as User

load_dotenv()

log = logging
log.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

updater = Updater(token=os.environ.get("TELEGRAM_BOT_TOKEN"), use_context=True)
dispatcher = updater.dispatcher

SETUP, MODE, BAND, CALLSIGN, CALLSIGN_SET, QSO = range(6)

callsign_regex_simple = r"[a-zA-Z0-9]{1,3}[0123456789][a-zA-Z0-9]{0,3}[a-zA-Z]"


def autolog(id):
    "Automatically log the current function details."
    import inspect, logging

    func = inspect.currentframe().f_back.f_code
    logging.info(
        "User %s: called %s in %s:%i"
        % (id, func.co_name, func.co_filename, func.co_firstlineno)
    )


def help(update, context):
    user_id = update.message.from_user["id"]
    u = User(user_id)
    autolog(user_id)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Simpy send me a valid callsign in my chat and I will log it for you. \n\n"
        f"Example: <code>{u.station_callsign} 599</code> (can be lowercase)\n\n"
        f"Current band/mode is set to {u.band} {u.mode}. \n"
        f"Type <code>20m</code> or <code>cw</code> anytime to change.\n\n"
        f"The same applies for RS(T), try this: <code>589</code>\n\n"
        f"Use the /adif command to download the whole log later.\n\n"
        f"I collect no personal data. Worried? Ping my owner @LY2EN.\n\n",
        parse_mode=ParseMode.HTML,
    )
    del u


def start(update, context):
    fname = update.message.from_user["first_name"]
    username = update.message.from_user["username"]
    user_id = update.message.from_user["id"]
    autolog(user_id)
    u = User(user_id)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Welcome, <b>{fname}</b>. I am your personal QSO logging bot.\n"
        f"You have <b>{u.qso_count}</b> QSOs in the log. ",
        parse_mode=ParseMode.HTML,
    )

    if u.station_callsign == "N0CALL":
        if re.match(callsign_regex_simple, username):
            u.set_station_callsign(username)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Your username (<b>{username}</b>) looks like a proper callsign.\n"
                f"I have set it as your primary station callsign. "
                f"Use the /station_callsign command to change this later.",
                parse_mode=ParseMode.HTML,
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Looks like you're using my services for the first time."
                "Use the /station_callsign command to set up your callsign.",
            )
        help(update, context)
    del u


def adif(update, context):
    user_id = update.message.from_user["id"]
    autolog(user_id)
    fname = update.message.from_user["first_name"]
    u = User(user_id)
    log_date = date.today().strftime("%Y%m%d")
    log_time = datetime.utcnow().strftime("%H%M%S")
    log_datetime = f"{log_date} {log_time}"
    log_file = (
        f"ADIF export from Telegram hamlogger bot @qso_log_bot (c) LY2EN\n\n"
        f"---\n Callsign : {u.station_callsign}\nName : {fname} \n---\n\n"
        f"<CREATED_TIMESTAMP:{len(log_datetime)}>{log_date} {log_time}\n"
        f"<PROGRAMID:11>QSO_LOG_BOT\n\n"
        f"<EOH>\n\n"
    )
    qso_db = sqlite3.connect("qso.db")
    cursor = qso_db.cursor()
    all_qsos = cursor.execute(
        "SELECT qso_date, time_on, mode, band, station_callsign, callsign as call, rst_sent, rst_rcvd "
        "FROM qso WHERE user_id=:user_id",
        {"user_id": user_id},
    ).fetchall()
    qso_db.close()
    if len(all_qsos) == 0:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Your log is empty. Try entering a callsign to log your first QSO!",
        )
        return

    for qso in all_qsos:
        log_file += f"<QSO_DATE:{len(str(qso[0]))}>{qso[0]} "
        log_file += f"<TIME_ON:{len(str(qso[1]))}>{qso[1]} "
        log_file += f"<MODE:{len(str(qso[2]))}>{qso[2]} "
        log_file += f"<BAND:{len(str(qso[3]))}>{qso[3]} "
        log_file += f"<STATION_CALLSIGN:{len(str(qso[4]))}>{qso[4]} "
        log_file += f"<CALL:{len(str(qso[5]))}>{qso[5]} "
        log_file += f"<RST_SENT:{len(str(qso[6]))}>{qso[6]} "
        log_file += f"<RST_RCVD:{len(str(qso[7]))}>{qso[7]} "
        log_file += "<EOR>\n"
    filename = f"logs/{u.station_callsign}-ADIF.txt"
    with open(filename, "w") as adif_file:
        adif_file.write(log_file)
        adif_file.flush()
        adif_file.close()
    with open(filename, "rb") as adif_file:
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=adif_file,
            filename=f"{u.station_callsign}-ADIF.txt",
        )
    del u


def create_qso_entry(update, context):
    user_id = update.message.from_user["id"]
    u = User(user_id)
    autolog(user_id)
    callsign = update.message.text.split(" ")[0].upper()
    qso_date = date.today().strftime("%Y%m%d")
    time_on = datetime.utcnow().strftime("%H%M%S")
    if u.station_callsign == "N0CALL":
        update.message.reply_text(
            f"Your callsign is set to {u.station_callsign}. Please make sure to change it with /station_callsign"
        )

    qso_db = sqlite3.connect("qso.db")
    cursor = qso_db.cursor()
    cursor.execute(
        "INSERT INTO qso VALUES (?, ?, ?, ?, ?, 100, ?, ?, 599, 599, '', '', 'DX')",
        (user_id, qso_date, time_on, u.mode, u.band, u.station_callsign, callsign),
    )
    qso_db.commit()
    update.message.reply_text(
        f"New QSO: {callsign} {u.band} {u.mode} at {qso_date}, {time_on}UTC"
    )
    qso_db.close()
    del u


def delete_last_qso(update, context):
    user_id = update.message.from_user["id"]
    u = User(user_id)
    autolog(user_id)
    qso_db = sqlite3.connect("qso.db")
    cursor = qso_db.cursor()
    cursor.execute(
        "DELETE FROM qso WHERE user_id=:user_id ORDER BY qso_date desc, time_on desc LIMIT 1;",
        {"user_id": user_id},
    )
    qso_db.commit()
    del u
    # refresh user object
    u = User(user_id)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"OK deleted last QSO. Your log now has {u.qso_count} entries",
    )
    del u


def set_mode(update, context):
    query = update.callback_query
    user_id = query.from_user["id"]
    autolog(user_id)
    u = User(user_id)
    u.set_mode(query.data)
    query.answer()
    query.edit_message_text(text=f"Mode set to: {query.data}")
    return


def set_mode_inline(update, context):
    user_id = update.message.from_user["id"]
    autolog(user_id)
    u = User(user_id)
    mode = update.message.text.upper()
    u.set_mode(mode)
    update.message.reply_text(f"Mode set to: {mode}")
    del u


def set_rst_inline(update, context):
    user_id = update.message.from_user["id"]
    autolog(user_id)
    u = User(user_id)
    rst = update.message.text.lower()
    u.set_srst(rst)
    update.message.reply_text(f"Default sRS(T) now: {rst}")
    del u


def set_band_inline(update, context):
    user_id = update.message.from_user["id"]
    autolog(user_id)
    u = User(user_id)
    band = update.message.text.lower()
    u.set_band(band)
    update.message.reply_text(f"Band set to: {band}")
    del u


def select_mode(update, context):
    options = [
        [
            InlineKeyboardButton(text="SSB", callback_data="SSB"),
            InlineKeyboardButton(text="CW", callback_data="CW"),
            InlineKeyboardButton(text="FM", callback_data="FM"),
            InlineKeyboardButton(text="FT8", callback_data="FT8"),
        ],
        [
            InlineKeyboardButton(text="WSPR", callback_data="WSPR"),
            InlineKeyboardButton(text="RTTY", callback_data="RTTY"),
            InlineKeyboardButton(text="SSTV", callback_data="SSTV"),
            InlineKeyboardButton(text="JT65", callback_data="JT65"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(options)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Please select operating mode:",
        reply_markup=reply_markup,
    )
    return MODE


def select_station_callsign(update, context):
    user_id = update.message.from_user["id"]
    autolog(user_id)
    u = User(user_id)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Your callsign is now set to {u.station_callsign}. "
        f"Please type in your new station callsign (type `.` to cancel):",
    )
    log.info(f"exiting with {CALLSIGN}")
    return CALLSIGN


def set_station_callsign(update, context):
    query = update.callback_query
    user_id = update.message.from_user["id"]
    autolog(user_id)
    u = User(user_id)
    station_callsign = update.message.text.upper()
    if station_callsign != ".":
        u.set_station_callsign(station_callsign)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Your callsign is now set to {u.station_callsign}.",
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Your callsign is unchanged: {u.station_callsign}.",
        )
    del u
    return CALLSIGN_SET


def set_band(update, context):
    pass


def select_band(update, context):
    pass


callsign_handler = MessageHandler(
    Filters.regex(callsign_regex_simple), create_qso_entry
)


select_mode_handler = ConversationHandler(
    entry_points=[CommandHandler("mode", select_mode)],
    states={MODE: [CallbackQueryHandler(set_mode)]},
    fallbacks=[CommandHandler("mode", select_mode)],
)


station_callsign_handler = ConversationHandler(
    entry_points=[CommandHandler("station_callsign", select_station_callsign)],
    states={
        CALLSIGN: [MessageHandler(Filters.all, set_station_callsign)],
        CALLSIGN_SET: [callsign_handler],
    },
    fallbacks=[CommandHandler("station_callsign", select_station_callsign)],
)


dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help))
dispatcher.add_handler(CommandHandler("adif", adif))
dispatcher.add_handler(CommandHandler("del", delete_last_qso))
dispatcher.add_handler(select_mode_handler)


dispatcher.add_handler(
    MessageHandler(
        Filters.regex(
            re.compile(
                r"^(AM|ARDOP|ATV|C4FM|CHIP|CLO|CW|DOMINO|DSTAR|FAX|FM|FSK441|"
                "FT8|HELL|ISCAT|JT.*|MFSK|MT63|OLIVIA|OPERA|PAC|PAX|PKT|PSK|"
                "PSK2K|Q15|QRA64|ROS|RTTY|RTTYM|SSB|SSTV|T10|THOR|THRB|TOR|V4"
                "|VOI|WINMOR|WSPR|AMTORFEC|ASCI|CHIP.*|DOMINOF|FMHELL|FSK31|"
                "GTOR|HELL.*|HFSK|JT4.*|JT65.*|MFSK.*|PAC.*|PAX2|PCW|Q{0,1}"
                "PSK.*|THRBX)$",
                re.IGNORECASE,
            )
        ),
        set_mode_inline,
    )
)

dispatcher.add_handler(
    MessageHandler(
        Filters.regex(
            r"^[0-9\.]+[cm]{0,1}m$",
        ),
        set_band_inline,
    )
)

dispatcher.add_handler(
    MessageHandler(
        Filters.regex(
            r"^[1-5][0-9]{1,2}$",
        ),
        set_rst_inline,
    )
)

dispatcher.add_handler(station_callsign_handler)
dispatcher.add_handler(callsign_handler)

if __name__ == "__main__":
    telegram_thread = Thread(target=updater.start_polling)
    telegram_thread.start()
