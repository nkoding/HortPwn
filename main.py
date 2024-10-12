# main.py

import csv
import json
import time
from hortapi import HortApi
from models import PresencesPerUser
import subprocess
import os
from datetime import datetime, timedelta, time as dtime
import logging
from logging.handlers import RotatingFileHandler

# Define application directory and test file path
app_dir = os.path.dirname(os.path.abspath(__file__))
test_file_path = os.path.join(app_dir, 'test')

# Configure logging with RotatingFileHandler
handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=2)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())

# Determine the path to signal-cli
script_dir = os.path.dirname(os.path.abspath(__file__))
signal_cli_path = os.path.join(script_dir, 'bin', 'signal-cli')

# Check if signal-cli exists
if not os.path.isfile(signal_cli_path):
    logger.error(f"signal-cli not found at: {signal_cli_path}")
    exit()

# Check permissions
if not os.access(signal_cli_path, os.X_OK):
    logger.error(f"signal-cli is not executable. Ensure permissions are set correctly: {signal_cli_path}")
    exit()

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    logger.info("Configuration file 'config.json' loaded successfully.")
    logger.debug(f"Configuration content: {config}")
except FileNotFoundError:
    logger.error("Configuration file 'config.json' not found. Ensure it is in the same directory as 'main.py'.")
    exit()
except json.JSONDecodeError as e:
    logger.error(f"Error parsing 'config.json': {e}")
    exit()
except Exception as e:
    logger.error(f"Unexpected error loading 'config.json': {e}")
    exit()

SIGNAL_NUMBER = config.get("signal_number")
HORTPRO_EMAIL = config.get("hortpro_login", {}).get("email")
HORTPRO_PASSWORD = config.get("hortpro_login", {}).get("password")
CHECK_INTERVAL = config.get("check_interval_seconds", 60)
COOKIE_PATH = config.get("cookie_path", "cookie.txt")
SIGNAL_CLI_RELATIVE_PATH = config.get("signal_cli_path", "bin/signal-cli")
signal_cli_path = os.path.join(script_dir, SIGNAL_CLI_RELATIVE_PATH)

# Check if all necessary configuration data is present
if not SIGNAL_NUMBER or not HORTPRO_EMAIL or not HORTPRO_PASSWORD:
    logger.error("Missing configuration data. Check 'config.json' for 'signal_number', 'hortpro_login.email', and 'hortpro_login.password'.")
    exit()

# Load recipients (individuals and groups)
try:
    if os.path.exists("chat_ids.json"):
        with open("chat_ids.json", "r") as f:
            chat_ids = json.load(f)
        logger.info(f"{len(chat_ids)} recipients loaded from 'chat_ids.json'.")
        logger.debug(f"Recipient list: {chat_ids}")
    else:
        chat_ids = []
        logger.info("No recipients found. Please add recipients using 'add_recipient.py'.")
except json.JSONDecodeError as e:
    logger.error(f"Error parsing 'chat_ids.json': {e}")
    chat_ids = []
except Exception as e:
    logger.error(f"Unexpected error loading 'chat_ids.json': {e}")
    chat_ids = []

def send_signal_message(recipient: str, recipient_type: str, message: str):
    try:
        if recipient_type == "individual":
            cmd = [
                signal_cli_path, "--verbose", "-u", SIGNAL_NUMBER, "send", "-m", message, recipient
            ]
        elif recipient_type == "group":
            cmd = [
                signal_cli_path, "--verbose", "-u", SIGNAL_NUMBER, "send", "-g", recipient, "-m", message
            ]
        else:
            logger.warning(f"Unknown recipient type: {recipient_type}")
            return

        logger.debug(f"Sending message to {recipient_type} {recipient}: {message}")
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"Message sent to {recipient}: {message}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error sending message to {recipient}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending message to {recipient}: {e}")

def monitor_presences(hort_api, kid_id, presences_per_users):
    presences = hort_api.get_presences(kid_id)
    if not presences:
        logger.warning("No presence data retrieved.")
        return

    today = datetime.now().date()
    try:
        today_presence = next(
            (
                item
                for item in presences.get("rows", [])
                if datetime.fromisoformat(item["date_start"]).date() == today
            ),
            None,
        )
    except KeyError as e:
        logger.error(f"Missing key in presence data: {e}")
        return
    except ValueError as e:
        logger.error(f"Error parsing date: {e}")
        return

    if not today_presence:
        logger.info("No presence data found for today.")
        return

    start_date = today_presence.get("date_start")
    end_date = today_presence.get("date_end")

    logger.debug(f"Today's presence data: Start: {start_date}, End: {end_date}")

    for chat in chat_ids:
        recipient = chat["id"]
        recipient_type = chat["type"]
        presence = presences_per_users.get(recipient, PresencesPerUser(recipient_id=recipient, recipient_type=recipient_type).presence)

        # Check-In
        if start_date and not presence.start_msg_sent:
            try:
                formatted_start = datetime.fromisoformat(start_date).strftime('%H:%M')
                message = f"Your child has been at the daycare since {formatted_start}."
                send_signal_message(recipient, recipient_type, message)
                presence.start_msg_sent = True
                logger.info(f"Check-In message sent to {recipient}.")
            except Exception as e:
                logger.error(f"Error sending Check-In message to {recipient}: {e}")

        # Check-Out
        if end_date and not presence.end_msg_sent:
            try:
                formatted_end = datetime.fromisoformat(end_date).strftime('%H:%M')
                message = f"Your child left the daycare at {formatted_end}."
                send_signal_message(recipient, recipient_type, message)
                presence.end_msg_sent = True
                logger.info(f"Check-Out message sent to {recipient}.")
            except Exception as e:
                logger.error(f"Error sending Check-Out message to {recipient}: {e}")

        # Update the presence status
        presences_per_users[recipient] = presence

    try:
        with open("presences_per_users.json", "w") as f:
            json.dump(
                {k: v.__dict__ for k, v in presences_per_users.items()},
                f,
                indent=4,
            )
        logger.debug("Presence data updated and saved.")
    except Exception as e:
        logger.error(f"Error saving presence data: {e}")

def load_schedule(schedule_file='scheduler.csv'):
    schedule = {}
    try:
        with open(schedule_file, mode='r') as csvfile:
            reader = csv.DictReader(filter(lambda row: not row.strip().startswith('#'), csvfile))
            for row in reader:
                day = row['day_of_week'].strip().lower()
                start_time = datetime.strptime(row['start_time'], '%H:%M').time()
                end_time = datetime.strptime(row['end_time'], '%H:%M').time()
                schedule.setdefault(day, []).append((start_time, end_time))
        logger.info(f"Schedule loaded from {schedule_file}.")
    except Exception as e:
        logger.error(f"Error loading schedule from {schedule_file}: {e}")
    return schedule

def get_next_window_start(now, schedule):
    weekday_str = now.strftime('%A').lower()
    today_schedule = schedule.get(weekday_str, [])

    for window in today_schedule:
        start, _ = window
        window_start_dt = datetime.combine(now.date(), start)
        if now < window_start_dt:
            return window_start_dt

    # Find next day with schedule
    days_ahead = 1
    while days_ahead <= 7:
        next_day = now + timedelta(days=days_ahead)
        weekday_str = next_day.strftime('%A').lower()
        next_day_schedule = schedule.get(weekday_str, [])
        if next_day_schedule:
            return datetime.combine(next_day.date(), next_day_schedule[0][0])
        days_ahead +=1
    return None

def run_test_mode():
    logging.info("Test mode file found. Running test mode.")
    for i in range(2):
        logging.info("Simulating child check-in...")
        for chat in chat_ids:
            send_signal_message(chat["id"], chat["type"], "Test Mode: Your child has checked in.")
        time.sleep(60)

        logging.info("Simulating child check-out...")
        for chat in chat_ids:
            send_signal_message(chat["id"], chat["type"], "Test Mode: Your child has checked out.")
        time.sleep(60)

    # Delete the test file after completing test runs
    os.remove(test_file_path)
    logging.info("Test mode completed. Test file deleted. Resuming normal operation.")

def main_loop():
    schedule = load_schedule()

    presences_per_users = {}

    while True:
        try:
             # Check if test mode file exists
            if os.path.isfile(test_file_path):
                run_test_mode()
            now = datetime.now()
            weekday_str = now.strftime('%A').lower()
            current_time = now.time()

            today_schedule = schedule.get(weekday_str, [])

            within_window = False
            current_window_end = None
            for window in today_schedule:
                start, end = window
                if start <= current_time <= end:
                    within_window = True
                    current_window_end = datetime.combine(now.date(), end)
                    break

            if within_window:
                logger.info(f"Current time: {now.strftime('%H:%M')}. Starting scraper.")
                hort_api = HortApi(email=HORTPRO_EMAIL, password=HORTPRO_PASSWORD, cookie_path=COOKIE_PATH)
                kid_id = hort_api.get_kid_id()
                if kid_id:
                    monitor_presences(hort_api, kid_id, presences_per_users)
                else:
                    logger.error("No child found. Skipping this window.")

                sleep_seconds = (current_window_end - now).total_seconds()
                if sleep_seconds >0:
                    logger.info(f"Sleeping until end of current window at {current_window_end.strftime('%H:%M')}. ({int(sleep_seconds)} seconds)")
                    time.sleep(sleep_seconds)
            else:
                next_window_start = get_next_window_start(now, schedule)
                if next_window_start:
                    sleep_seconds = (next_window_start - now).total_seconds()
                    logger.info(f"Outside time windows. Sleeping until next window at {next_window_start.strftime('%Y-%m-%d %H:%M')}. ({int(sleep_seconds)} seconds)")
                    if sleep_seconds >0:
                        time.sleep(sleep_seconds)
                else:
                    logger.info("No scheduled windows found. Sleeping for 1 hour.")
                    time.sleep(3600)

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    logger.info("HortPro Signal Notifier started.")
    main_loop()
