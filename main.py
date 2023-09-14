import os
import time
import urllib.parse
import base64
import hmac
from hashlib import sha1
import requests
import csv
import json

BASE_URL = "https://mdmenrollment.apple.com"
SESSION_URI = "/session"
DEVICE_ENDPOINT = "/devices"
TOKEN_REFRESH_RATE = 1000
USER_AGENT = "YourUserAgentHere"
LOG_FILE = "log/log.txt"
DEVICE_SERIAL_NUMBERS_FILE = "data/deviceSerialNumbers.csv"
RESULT_FILE = "output/result.txt"
CHECK_POINT_FILE = "output/checkpoint.txt"
STATUS_COUNT_FILE = "output/status_counts.json"


def ensure_path_exists(path):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def open_with_path_creation(path, mode='r', **kwargs):
    ensure_path_exists(path)
    return open(path, mode, **kwargs)


log_file = open_with_path_creation(LOG_FILE, 'w', encoding='utf-8', buffering=1)  # Line buffering mode


def load_credentials():
    with open_with_path_creation('./config/credentials.json', 'r') as f:
        return json.load(f)


CREDENTIAL_CONFIG = load_credentials()


def log_and_write(message):
    print(message)
    log_file.write(message + '\n')


def get_session_token():
    for _ in range(3):  # retry up to 3 times
        timestamp = int(time.time())
        nonce = int(time.time() * 1000) % 1000000

        oauth_params = {
            "oauth_consumer_key": CREDENTIAL_CONFIG["oauth_consumer_key"],
            "oauth_token": CREDENTIAL_CONFIG["oauth_token"],
            "oauth_signature_method": CREDENTIAL_CONFIG["oauth_signature_method"],
            "oauth_timestamp": str(timestamp),
            "oauth_nonce": str(nonce),
            "oauth_version": CREDENTIAL_CONFIG["oauth_version"]
        }

        base_string = f"GET&{urllib.parse.quote_plus(BASE_URL + SESSION_URI)}&"
        base_string += urllib.parse.quote_plus('&'.join(f"{key}={oauth_params[key]}" for key in sorted(oauth_params)))

        signing_key = f"{CREDENTIAL_CONFIG['oauth_consumer_secret']}&{CREDENTIAL_CONFIG['oauth_secret']}"
        signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), sha1).digest())

        oauth_params["oauth_signature"] = signature.decode()
        auth_header = "OAuth " + ', '.join(f'{key}="{oauth_params[key]}"' for key in oauth_params)

        headers = {
            "User-Agent": USER_AGENT,
            "Authorization": auth_header
        }

        response = requests.get(BASE_URL + SESSION_URI, headers=headers)
        log_and_write(f"session: {response.text}")

        if response.status_code == 200:
            return response.json()["auth_session_token"]

        if "oauth_problem_adviceBad Request" in response.text:
            time.sleep(10)
        else:
            response.raise_for_status()

    raise Exception("Failed to get session token after 3 attempts.")


def fetch_device_details(auth_token, serial_number, total_checked, total_rows):
    for _ in range(3):  # retry up to 3 times
        headers = {
            "User-Agent": USER_AGENT,
            "X-ADM-Auth-Session": auth_token,
            "Content-Type": "application/json"
        }
        payload = {
            "devices": [serial_number]
        }
        response = requests.post(BASE_URL + DEVICE_ENDPOINT, headers=headers, data=json.dumps(payload))
        log_and_write(f"response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            log_and_write(
                f"[{total_checked}/{total_rows}] Success for serial_number: {serial_number}, {json.dumps(data, separators=(',', ':'))}")
            return data.get("devices", {}).get(serial_number, {}).get("response_status", "UNKNOWN_STATUS")

        log_and_write(
            f"[{total_checked}/{total_rows}] FAILED for serial_number: {serial_number}, response: {response.text}")

        if response.status_code != 401:
            time.sleep(10)
        else:
            return "ERROR_STATUS_CODE"

    return "UNKNOWN_STATUS_AFTER_RETRIES"


def load_checkpoint():
    if os.path.exists(CHECK_POINT_FILE):
        with open_with_path_creation(CHECK_POINT_FILE, "r") as f:
            return int(f.read().strip())
    return 0


def save_checkpoint(index):
    with open_with_path_creation(CHECK_POINT_FILE, "w") as f:
        f.write(str(index))


def load_status_counts():
    if os.path.exists(STATUS_COUNT_FILE):
        with open_with_path_creation(STATUS_COUNT_FILE, "r") as f:
            return json.load(f)
    return {}


def save_status_counts(status_counts):
    with open_with_path_creation(STATUS_COUNT_FILE, "w") as f:
        json.dump(status_counts, f)


def main():
    log_and_write("Starting the script...")
    last_processed_index = load_checkpoint()
    auth_token = get_session_token()
    total_checked = last_processed_index
    status_counts = load_status_counts()

    with open_with_path_creation(DEVICE_SERIAL_NUMBERS_FILE, 'r') as f:
        total_rows = sum(1 for row in f)
        f.seek(0)
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if idx < last_processed_index:
                continue

            serial_number = row[0]

            if total_checked % TOKEN_REFRESH_RATE == 0 and total_checked != 0:
                auth_token = get_session_token()

            response_status = fetch_device_details(auth_token, serial_number, total_checked, total_rows)
            log_and_write(response_status)

            status_counts.setdefault(response_status, []).append(serial_number)
            save_status_counts(status_counts)
            total_checked += 1
            save_checkpoint(total_checked)

    with open_with_path_creation(RESULT_FILE, 'w') as f:
        for status, devices in status_counts.items():
            f.write(f'"{status}", {len(devices)}\n')
            for device in devices:
                f.write(device + '\n')
            f.write('\n')

    log_and_write(f"Total Checked: {total_checked}")


if __name__ == "__main__":
    main()