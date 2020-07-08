# Soracom connectivity benchmark test

This python script is a utility to record the time taken by Soracom sim to change status from Ready to Active on the console

## Requirements
- This script requires python 2 or above
- The following python libraries must be installed:
  - pip install pyserial
  - pip install requests
- The Soracom credentials must be set in the environment variables before running and Soracom sim must be connected in a modem
  - SORACOM_AUTH_KEY_ID
  - SORACOM_AUTH_KEY
- Edit the script and set the correct serial port for the modem

Then run the script as follows:
- python soracom_benchmark_test.py
