# Homebridge Sensor Data Collector

## Overview
The Homebridge Sensor Data Collector is a Python-based tool for periodically collecting sensor data from Homebridge-enabled devices. The script interfaces with the Homebridge API to retrieve data, such as temperature readings, and stores it in Perquet files for further analysis and usage.

## Features
- Fetches sensor data from Homebridge API.
- Stores data in local Perquet files

## Prerequisites

- Homebridge setup with accessible API

## Setup and Configuration

### 1. Configure Homebridge API Access
Before running the script, ensure your Homebridge API is set up and accessible. You will need the following information:

- Homebridge username and password
- Homebridge API URL (should be the URL to access your Homebridge)
- Homebridge Device URL (each device has a unique URL)

### 2. Configuration File (.env)
Edit the ```.env``` file with your Homebridge details:

```shell
API_USERNAME=YOUR_HOMEBRIDGE_USERNAME
API_PASSWORD=YOUR_HOMEBRIDGE_PASSWORD
API_OPT=YOUR_ONE_TIME_PASSWORD_IF_USED
API_BASE_DEVICE_URL=http://YOUR_HOMEBRIDGE_IP:PORT/
API_LOGIN_URL=http://YOUR_HOMEBRIDGE_IP:PORT/api/auth/login
API_DEVICE_URL=http://YOUR_HOMEBRIDGE_IP:PORT/api/accessories/YOUR_DEVICE_UNIQUE_ID
PARQUET_FOLDER_PATH=PATH_FOR_PARQUET_FILES
```
- Replace `YOUR_HOMEBRIDGE_USERNAME` and `YOUR_HOMEBRIDGE_PASSWORD` with your Homebridge credentials.
- Adjust `YOUR_HOMEBRIDGE_IP` and `PORT` to match your Homebridge server address and port.
- For `YOUR_DEVICE_UNIQUE_ID`, refer to your Homebridge device's unique identifier. See instructions for obtaining it below
- For `PARQUET_FOLDER_PATH`, enter the absolute path of where the parquet files should be stored. 

#### Automated: Obtaining Device Unique ID using Python
- Fill out the configuration file (```.env```) with the ```API_USERNAME```, ```API_PASSWORD```, ```API_OPT```, and ```API_BASE_DEVICE_URL``` values. 
- Run the ```collect-homebridge-device-information.py``` program
- Open the newly generated ```homebridge-device-information.json``` file. It is recommended that the text editor used to open the file be able to format it to be more readable. 
- The file will have a list of JSON objects, one object per accessory. Look for the JSON object describing the sensor you are attempting to pull data from. At the end of that JSON object for that sensor is a field called ```uniqueId```, that is the value needed. 

```json
{
        "aid": 2,
        "iid": 8,
        "uuid": "0000004A-0000-...",
        "type": "Thermostat",
        "humanType": "Thermostat",
        "serviceName": "Thermostat",
        "serviceCharacteristics": [
            ...
        ]
        "instance": {
            "name": "homebridge",
            "username": "...",
            "ipAddress": "...",
            "port": ...,
            "services": [],
            "connectionFailedCount": 0,
            "configurationNumber": "3"
        },
        "uniqueId": "f3cdb82ffd757cebbcb136ac384e4331e805cfe082dab2e181044b0b33c65b67"
}
```
- Add this ```uniqueID``` to the API_DEVICE_URL variable in the .env file

#### Manual: Obtaining Device Unique ID using Swagger UI

To obtain the unique ID of your device through the Homebridge API using Swagger UI, you need to first get an authentication token and then use this token to access the device information. Here’s how to do it step-by-step:

##### Step 1: Getting an Authentication Token
-  **Access Swagger UI:** Open your web browser and navigate to the Swagger UI for your Homebridge instance. The URL typically looks like `http://YOUR_HOMEBRIDGE_IP:PORT/swagger#`

- **Use /api/auth/login Endpoint**: In Swagger UI, find and select the /api/auth/login endpoint. This endpoint is used for authenticating and obtaining a token.

- **Enter Credentials**: In the request body section of this endpoint, enter your Homebridge username, password, and one-time password (OTP). Note that it is required to pass the ```opt``` field and value in the JSON even if one is not needed for authentication. It should look like this:

```json
{
  "username": "admin",
  "password": "admin",
  "otp": "optional-otp"
}
```


- **Execute Request**: Click the 'Execute' button to send the request.

- **Copy the Token**: Once the request is successful, you will receive a response that includes the access_token. Copy this token as it will be used in the next step.

Example Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "Bearer",
  "expires_in": 28800
}
```


##### Step 2: Getting the Unique Device ID
- **Navigate to /api/accessories Endpoint**: In Swagger UI, locate the /api/accessories endpoint.

- **Use the Token**: In the authorization section of this endpoint, enter the token you obtained earlier. It should be included as a Bearer token in the header.

- **Execute Request**: Click 'Execute' to send the request with the token.

- **Find the Unique ID**: The response will include a list of all connected Homebridge accessories. Look through the list to find the unique ID of the device you are interested in.

- **Add this device ID to the API_DEVICE_URL variable in the .env file**


## Running the process

Simply run ```python collector.py``` to begin the retreival process. Note that the shell used my need higher level privileges, depending on the permissions of the directory storing the Parquet files. 