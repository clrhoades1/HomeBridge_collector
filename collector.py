import datetime
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv
from filelock import FileLock

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

LOCK_FILE = "/tmp/collector.lock"
LOG_LINE_PATTERN = re.compile(
    r".*?\[(?P<timestamp>\d{1,2}/\d{1,2}/\d{4},\s*\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM))\].*?\[\s*eWeLink\s*\](?:\[\d+m\]?)?.*?\[(?P<device>[^\]]+)\].*?\[(?P<power>[^\]]+)\](?:.*?\[(?P<voltage>[^\]]+)\])?(?:.*?\[(?P<current>[^\]]+)\])?"
)


def generate_parquet_file_name(type):
    return type + "-sensor-" + datetime.today().strftime("%Y-%m-%d") + ".parquet"


# Function to login and retrieve the access token
def login():
    credentials = {
        "username": os.getenv("API_USERNAME"),
        "password": os.getenv("API_PASSWORD"),
        "otp": os.getenv("API_OTP"),
    }
    login_url = os.getenv("API_LOGIN_URL")
    response = requests.post(login_url, json=credentials)
    response.raise_for_status()
    token_info = response.json()
    return token_info["access_token"], datetime.now() + timedelta(
        seconds=token_info["expires_in"]
    )


def insert_to_google_sheet(action, sensor):
    payload = {"action": action, "sensor": sensor}
    response = requests.get(
        os.getenv("GOOGLE_SHEET_SCRIPT_URL"),
        params=payload,
    )
    print(response.content)


# Function to insert data into Parquet File
def insert_thermostat_data(
    timestamp, device_id, device_name, current_temperature, target_temperature
):
    parquet_file_name = (
        os.getenv("PARQUET_FOLDER_PATH")
        + ""
        + generate_parquet_file_name("temperature")
    )

    # Read existing Parquet file to DataFrame (if it exists)
    parquet_df = pd.DataFrame()

    if os.path.exists(parquet_file_name):
        parquet_df = pd.read_parquet(parquet_file_name)

    # Check if this is new data
    is_new = True
    if not parquet_df.empty:
        last_entry = parquet_df.iloc[-1]
        # Compare current and target temperature (ignore timestamp)
        if (
            last_entry["current temperature"] == current_temperature
            and last_entry["target temperature"] == target_temperature
        ):
            is_new = False

    # Always append to Parquet
    parquet_df = pd.concat(
        [
            parquet_df,
            pd.DataFrame(
                {
                    "timestamp": [timestamp],
                    "device name": [device_name],
                    "current temperature": [current_temperature],
                    "target temperature": [target_temperature],
                }
            ),
        ],
        ignore_index=True,
    )

    # Write DataFrame back to the file
    parquet_df.to_parquet(parquet_file_name)

    # Only send to Google Sheet if data is new
    if is_new:
        insert_to_google_sheet(current_temperature, device_name)


def is_latest_data_new(previous_item: pd.DataFrame, new_item: pd.DataFrame):
    if previous_item.empty:
        return True

    latest_item = new_item.tail(1).reset_index(drop=True)
    previous_item = previous_item.reset_index(drop=True)

    # Compare only value columns, not timestamps.
    latest_item = latest_item.drop("timestamp", axis=1, errors="ignore")
    previous_item = previous_item.drop("timestamp", axis=1, errors="ignore")

    # Return True when the latest row is different from the previous row (new data).
    return not latest_item.equals(previous_item)


def insert_switch_data(timestamp, device_id, device_name, is_on, outlet_in_use):
    parquet_file_name = (
        os.getenv("PARQUET_FOLDER_PATH") + "" + generate_parquet_file_name("switch")
    )

    # Read existing Parquet file to DataFrame (if it exists)
    parquet_df = pd.DataFrame()

    if os.path.exists(parquet_file_name):
        parquet_df = pd.read_parquet(parquet_file_name)

    # Check if this is new data for the device
    is_new = True
    if not parquet_df.empty:
        device_entries = parquet_df[parquet_df["device name"] == device_name]
        if not device_entries.empty:
            last_entry = device_entries.iloc[-1]
            # Compare is_on and Outlet in use (ignore timestamp)
            if (
                last_entry["is on"] == is_on
                and last_entry["Outlet in use"] == outlet_in_use
            ):
                is_new = False

    # Always append to Parquet
    parquet_df = pd.concat(
        [
            parquet_df,
            pd.DataFrame(
                {
                    "timestamp": [timestamp],
                    "device name": [device_name],
                    "is on": [is_on],
                    "Outlet in use": [outlet_in_use],
                }
            ),
        ],
        ignore_index=True,
    )

    # Write DataFrame back to the file
    parquet_df.to_parquet(parquet_file_name)

    # Only send to Google Sheet if data is new
    if is_new:
        json_attributes = generate_json_attributes("is_on", is_on, "outlet_in_use", outlet_in_use)
        insert_to_google_sheet(action=json_attributes, sensor=device_name)


def insert_log_data(timestamp, device_name, current_power, current_voltage, current_current):
    parquet_file_name = os.path.join(
        os.getenv("PARQUET_FOLDER_PATH", ""),
        generate_parquet_file_name("homebridge-log"),
    )

    parquet_df = pd.DataFrame()
    if os.path.exists(parquet_file_name):
        parquet_df = pd.read_parquet(parquet_file_name)

    # Check if this is new data for the device
    is_new = True
    if not parquet_df.empty:
        device_entries = parquet_df[parquet_df["device name"] == device_name]
        if not device_entries.empty:
            last_entry = device_entries.iloc[-1]
            # Compare power, voltage, current (ignore timestamp)
            if (
                last_entry["current power"] == current_power
                and last_entry["current voltage"] == current_voltage
                and last_entry["current current"] == current_current
            ):
                is_new = False

    # Always append to Parquet
    parquet_df = pd.concat(
        [
            parquet_df,
            pd.DataFrame(
                {
                    "timestamp": [timestamp],
                    "device name": [device_name],
                    "current power": [current_power],
                    "current voltage": [current_voltage],
                    "current current": [current_current],
                }
            ),
        ],
        ignore_index=True,
    )

    parquet_df.to_parquet(parquet_file_name)

    # Only send to Google Sheet if data is new
    if is_new:
        insert_to_google_sheet(
            action=json.dumps(
                {
                    "current_power": current_power,
                    "current_voltage": current_voltage,
                    "current_current": current_current,
                }
            ),
            sensor=device_name,
        )


def generate_json_attributes(attr1, value1, attr2, value2):
    return "{ " + attr1 + ": " + str(value1) + "," + attr2 + ": " + str(value2) + "}"

def process_thermostat(data, device_id):
    # TODO:  Need a better default value
    current_temperature = -255
    target_temperature = -255
    device_name = "unassigned"

    for service_characteristic in data["serviceCharacteristics"]:
        if service_characteristic["type"] == "CurrentTemperature":
            current_temperature = service_characteristic["value"]
            device_name = service_characteristic["serviceName"]
        if service_characteristic["type"] == "TargetTemperature":
            target_temperature = service_characteristic["value"]

    insert_thermostat_data(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        device_id,
        device_name,
        current_temperature,
        target_temperature,
    )


def process_switch(data, device_id):
    # TODO:  Need a better default value
    is_on = "unknown"
    device_name = "unassigned"
    outlet_in_use = 0

    for service_characteristic in data["serviceCharacteristics"]:
        if service_characteristic["type"] == "On":
            is_on = service_characteristic["value"]
            device_name = service_characteristic["serviceName"]
        if service_characteristic["type"] == "OutletInUse":
            outlet_in_use = service_characteristic["value"]

    insert_switch_data(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        device_id,
        device_name,
        is_on,
        outlet_in_use,
    )


# Function to query the Homebridge API
def query_homebridge_api(token, device_name, device_id):
    try:
        device_url = os.getenv("API_DEVICE_URL") + device_id
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(device_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Here is where we will query to get the values we want to extract.

        if device_name == "thermostat":
            process_thermostat(data, device_id)
        elif "switch" in device_name:
            process_switch(data, device_id)

    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")

def parse_homebridge_log(log_file_path=None, last_position=0):
    if not log_file_path:
        log_file_path = os.getenv("HOMEBRIDGE_LOG_FILE_PATH", "homebridge/homebridge.log")

    if not os.path.isfile(log_file_path):
        logging.warning("Homebridge log file not found: %s", log_file_path)
        return [], 0

    file_size = os.path.getsize(log_file_path)
    if last_position > file_size:
        last_position = 0

    parsed_entries = []
    with open(log_file_path, "r", encoding="utf-8", errors="ignore") as log_file:
        log_file.seek(last_position)
        for line in log_file:
            match = LOG_LINE_PATTERN.search(line)
            if not match:
                continue

            parsed_entries.append(
                {
                    "timestamp": match.group("timestamp").strip(),
                    "device_name": match.group("device").strip(),
                    "current_power": match.group("power").strip(),
                    "current_voltage": (match.group("voltage") or "").strip(),
                    "current_current": (match.group("current") or "").strip(),
                }
            )

        last_position = log_file.tell()

    return parsed_entries, last_position

def main():
    try:
        with FileLock(LOCK_FILE, timeout=1):
            token, token_expiry = login()
            # Assuming you have a file named 'example.json' with JSON content
            # example.json: {"product": "Laptop", "price": 1200}

            with open("./device-details.json", "r") as f:
                device_data = json.load(f)

            homebridge_log_path = os.getenv(
                "HOMEBRIDGE_LOG_FILE_PATH", "homebridge/homebridge.log"
            )
            log_file_position = 0

            while True:
                parsed_entries, log_file_position = parse_homebridge_log(
                    homebridge_log_path, log_file_position
                )
                for entry in parsed_entries:
                    logging.debug(
                        "Parsed Homebridge log entry: %s power=%s voltage=%s current=%s",
                        entry["device_name"],
                        entry["current_power"],
                        entry["current_voltage"],
                        entry["current_current"],
                    )
                    insert_log_data(
                        entry["timestamp"],
                        entry["device_name"],
                        entry["current_power"],
                        entry["current_voltage"],
                        entry["current_current"],
                    )

                for device_name, device_id in device_data.items():
                    if datetime.now() >= token_expiry:
                        token, token_expiry = login()

                    query_homebridge_api(token, device_name, device_id)
                time.sleep(10)  # Wait for 60 seconds before the next iteration
    except TimeoutError:
        print(
            f"Another instance of the program is already running with lock file: {LOCK_FILE}"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt was received")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if os.path.exists(LOCK_FILE):
            try:
                os.remove(LOCK_FILE)
                print(f"Removed stale lock file: {LOCK_FILE}")
            except OSError as e:
                print(f"Error removing lock file: {e}")


# Execute the main function
if __name__ == "__main__":
    main()
