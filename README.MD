# Soracom connectivity benchmark test

This python script is a utility to record the time taken by Soracom sim to change status from Ready to Active on the console

## Requirements
- This script requires python 2 or above and python-pip to install module dependency:
  - sudo apt install  python2.7 python-pip
- The following python libraries must be installed:
  - pip install pyserial
  - pip install requests
- The Soracom credentials must be set in the environment variables before running and Soracom sim must be connected in a modem
  - export SORACOM_AUTH_KEY_ID=<keyId>
  - export SORACOM_AUTH_KEY=<secret>
- Edit the script and set the correct serial port for the modem and preference for changing status from ready to active on the console
  - serial_port = "/dev/ttyUSB2" 
  - activate = False

NOTE: If Modem manager is installed on your device, you might want to stop it before starting
sudo service ModemManager stop

Then run the script as follows:
- python connectivity_benchmark.py

# Benchmark report
Benchmark report looks like this
```
# -----------------BENCHMARK STATISTICS-----------------
SIM ICCID 89423xxxxxxxxxxxxxx IMSI 295xxxxxxxxxxxx
Status                        : active
Online                        : True
Start time (after cache clear): 2020-07-08 06:24:37.603788
Network registered time       : 2020-07-08 06:24:46.784700
Console Online time           : 2020-07-08 06:24:53.562923
Time taken to register network: 0:00:09.180912
Time taken to come online     : 0:00:15.959135
# ------------------------------------------------------
```