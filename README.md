# AppleMDMDeviceChecker

## Introduction

AppleMDMDeviceChecker is a script designed to interface with Apple's MDM (Mobile Device Management) Enrollment API. This script helps fetch device details for a list of device serial numbers, logs response details, and categorizes the status of each device based on the received response.

## Features

1. **Session Token Management**: Authenticates and fetches session tokens from Apple's MDM service, handling retries if needed.
2. **Batch Device Details Retrieval**: Allows batch retrieval of device details by serial numbers from a CSV file.
3. **Logging**: Comprehensive logging mechanism, logs each step and API response.
4. **Checkpoint Mechanism**: Uses checkpoints to keep track of the last processed device. This way, the script can resume its operation after interruptions.
5. **Status Classification**: Categorizes devices by their response status for better reporting.

## How to Use

1. **Setup**: 

    - Ensure you have a `config` directory containing the `credentials.json` file which stores all necessary OAuth credentials to authenticate with Apple's MDM API.
    - Add a CSV file named `deviceSerialNumbers.csv` in the `data` directory, which lists all device serial numbers you want to check.

2. **Run Script**: 

    ```bash
    python AppleMDMDeviceChecker.py
    ```

3. **Log & Result Files**:
   
   - **Logs**: All logs can be found under `log/log.txt`.
   - **Results**: Processed results are stored in `output/result.txt` which contains the status and corresponding serial numbers.
   - **Checkpoints**: The last processed device index is stored in `output/checkpoint.txt`.
   - **Status Count**: Stores the count of each status in `output/status_counts.json`.

4. **Error Handling**:

    If the script encounters errors, it will make retries based on configured retry counts. After exhausting retries, it categorizes them as unknown statuses and continues processing.

> **Note**: Replace `YourUserAgentHere` with the appropriate user agent when configuring the script.