# Soracom connectivity benchmark test

This python script is a utility to record the time taken by Soracom sim to change status from Ready to Active on the console

## Requirements
- This script requires python 2 or above and python-pip to install module dependency:
  - sudo apt install  python2.7 python-pip
- The following python libraries must be installed:
  - pip install pyserial
  - pip install requests
- The Soracom credentials must be set in the environment variables before running and Soracom sim must be connected in a modem
  - export SORACOM_AUTH_KEY_ID=keyId
  - export SORACOM_AUTH_KEY=secret
- You may also override the default settings for the serial port of the modem and for the preference about changing status from ready to active on the console
  - export BENCHMARK_TEST_MODEM_PORT=/dev/ttyUSB0
  - export BENCHMARK_TEST_ACTIVATE_SIM=False
NOTE: If Modem manager is installed on your device, you might want to stop it before starting the test
sudo service ModemManager stop

Then run the script as follows:
- python connectivity_benchmark.py

# Benchmark report
Benchmark report looks like this

```
# -----------------BENCHMARK STATISTICS-----------------
SIM ICCID 89423xxxxxxxxxxxxxx IMSI xxxxxxxxxxxxxxx
Modem Manufacturer            : aaaaaa
Modem Model                   : bbbbbb
Modem Revision                : cccccc
Modem Serial number           : dddddd
Sim Status on console         : active
Online                        : True
Start time (after cache clear): 2020-07-10 12:21:39.232000
Network registered time       : 2020-07-10 12:22:39.550000
Console Online time           : 2020-07-10 12:22:43.493000
Time taken to register network: 0:01:00.318000
Time taken to come online     : 0:01:04.261000
Network registered            : +COPS: 0,0,"NNNNN",2
Signal quality                : +CSQ: 11,99
# ------------------------------------------------------
```
