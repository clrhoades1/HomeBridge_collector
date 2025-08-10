# Homebridge Sensor Data Collector

## Overview
The Homebridge Sensor Data Collector is a Python-based tool for periodically collecting sensor data from Homebridge-enabled devices. The script interfaces with the Homebridge API to retrieve data, such as temperature readings, and stores it in Perquet files for further analysis and usage.

## Features
Fetches sensor data from Homebridge API.
Stores data in local Perquet files
Easy to set up and run using Docker.

## Prerequisites

- Docker
- Homebridge setup with accessible API

## Setup and Configuration

### 1. Configure Homebridge API Access
Before running the script, ensure your Homebridge API is set up and accessible. You will need the following information:

- Homebridge username and password
- Homebridge API URL and Device URL

### 2. Configuration File (config.json)
Edit the config.json file with your Homebridge details:

```json
{
    "username": "YOUR_HOMEBRIDGE_USERNAME",
    "password": "YOUR_HOMEBRIDGE_PASSWORD",
    "otp": "YOUR_ONE_TIME_PASSWORD_IF_USED",
    "login_url": "http://YOUR_HOMEBRIDGE_IP:PORT/api/auth/login",
    "device_url": "http://YOUR_HOMEBRIDGE_IP:PORT/api/accessories/YOUR_DEVICE_UNIQUE_ID"
}
```
- Replace `YOUR_HOMEBRIDGE_USERNAME` and `YOUR_HOMEBRIDGE_PASSWORD` with your Homebridge credentials.
- Adjust `YOUR_HOMEBRIDGE_IP` and `PORT` to match your Homebridge server address and port.
- For `YOUR_DEVICE_UNIQUE_ID`, refer to your Homebridge device's unique identifier.

### Obtaining Device Unique ID using Swagger UI

To obtain the unique ID of your device through the Homebridge API using Swagger UI, you need to first get an authentication token and then use this token to access the device information. Here’s how to do it step-by-step:

Step 1: Getting an Authentication Token
-  **Access Swagger UI:** Open your web browser and navigate to the Swagger UI for your Homebridge instance. The URL typically looks like `http://YOUR_HOMEBRIDGE_IP:PORT/swagger#`

- Use /api/auth/login Endpoint: 
In Swagger UI, find and select the /api/auth/login endpoint. This endpoint is used for authenticating and obtaining a token.

- Enter Credentials: In the request body section of this endpoint, enter your Homebridge username, password, and one-time password (OTP) if used. It should look like this:

```json
{
  "username": "admin",
  "password": "admin",
  "otp": "optional-otp"
}
```

Execute Request: Click the 'Execute' button to send the request.

Copy the Token: Once the request is successful, you will receive a response that includes the access_token. Copy this token as it will be used in the next step.

Example Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "Bearer",
  "expires_in": 28800
}
```
Using Curl: Alternatively, you can use a curl command in a terminal or SSH session to get the token. Here's an example of the curl command:

```bash
curl -X 'POST' \
  'http://192.168.2.20:8181/api/auth/login' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
      "username": "admin",
      "password": "admin",
      "otp": "optional-otp"
  }'
```

Step 2: Getting the Unique Device ID
Navigate to /api/accessories Endpoint: In Swagger UI, locate the /api/accessories endpoint.

Use the Token: In the authorization section of this endpoint, enter the token you obtained earlier. It should be included as a Bearer token in the header.

Execute Request: Click 'Execute' to send the request with the token.

Find the Unique ID: The response will include a list of all connected Homebridge accessories. Look through the list to find the unique ID of the device you are interested in.

Curl Command: You can also use curl for this request:

```bash 
curl -X 'GET' \
  'http://192.168.2.20:8181/api/accessories' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

Replace YOUR_ACCESS_TOKEN with the token you obtained.

 ### Automation in the Script
 
In the collector.py script, the process of requesting and renewing the access token is automated. The script logs in to the Homebridge API using the credentials provided in config.json and stores the received token. Before each API call, it checks if the token is near expiration and automatically renews it if necessary. This ensures continuous and uninterrupted access to the API for data collection without manual intervention.

### 3. Building and Running with Docker

Run the following commands to build and run the Docker container:

```bash
docker build -t homebridge-collector .
docker run -d homebridge-collector
```
