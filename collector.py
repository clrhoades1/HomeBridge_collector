import requests
import logging
from datetime import datetime, timedelta
import time
import os
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

def generate_parquet_file_name():
    return "temperature-sensor-" + datetime.today().strftime('%Y-%m-%d') + ".parquet"


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
    return token_info['access_token'], datetime.now() + timedelta(seconds=token_info['expires_in'])

# Function to insert data into Parquet File
def insert_data(timestamp, device_id, current_temperature, target_temperature):
    parquet_file_name = os.getenv('PARQUET_FOLDER_PATH') + "" + generate_parquet_file_name()
    
    # Read existing Parquet file to DataFrame (if it exists)
    parquet_df = pd.DataFrame()

    if(os.path.exists(parquet_file_name)):
        parquet_df = pd.read_parquet(parquet_file_name)
    
    # Append new value to it
    parquet_df = pd.concat([parquet_df, pd.DataFrame({'timestamp': [timestamp], 'current temperature': [current_temperature], "target temperature": [target_temperature]})], ignore_index=True)
    
    # Write DataFrame back ot the file
    parquet_df.to_parquet(parquet_file_name)

    

# Function to query the Homebridge API
def query_homebridge_api(token):
    try:
        device_url = os.getenv('API_DEVICE_URL')
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(device_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Here is where we will query to get the values we want to extract. 
        
        current_temperature = data['values']['CurrentTemperature']
        target_temperature = data['values']['TargetTemperature']

        insert_data(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "34f747c785c7", current_temperature, target_temperature)

    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")

def main():
    try:
        token, token_expiry = login()

        while True:  
            if datetime.now() >= token_expiry:
                token, token_expiry = login()
            
            query_homebridge_api(token)
            time.sleep(60)  # Wait for 60 seconds before the next iteration

    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Execute the main function
if __name__ == "__main__":
    main()
