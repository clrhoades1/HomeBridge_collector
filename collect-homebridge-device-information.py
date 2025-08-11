import requests
import logging
from datetime import datetime, timedelta
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to login and retrieve the access token
def login():
    credentials = {
        "username": os.getenv('API_USERNAME'), 
        "password": os.getenv('API_PASSWORD'), 
        "otp": os.getenv('API_OTP')
    }
    login_url = os.getenv('API_LOGIN_URL')
    response = requests.post(login_url, json=credentials)
    response.raise_for_status()
    token_info = response.json()
    return token_info['access_token']


# Function to query the Homebridge API for the accessory information
def query_homebridge_api(token):
    try:
        api_url = os.getenv('API_BASE_DEVICE_URL')
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(api_url+"api/accessories", headers=headers)
        response.raise_for_status()

        with open("homebridge-device-information.json", "w") as f:
            f.write(json.dumps(response.json()))


    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")

def main():
    try:
        token= login()
        query_homebridge_api(token)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Execute the main function
if __name__ == "__main__":
    main()
