import os
import time
import serial
import requests
import json
from datetime import datetime

ACCESS_TECHNOLOGY_GSM = "0" #2G
ACCESS_TECHNOLOGY_UMTS = "2" #3G
ACCESS_TECHNOLOGY_EUTRAN = "7" #LTE

#Set these variables before starting
serial_port = os.environ.get('BENCHMARK_TEST_MODEM_PORT', '/dev/ttyUSB0') # Modem serial port Eg "COM6" or "/dev/ttyUSB0"
activate = os.environ.get('BENCHMARK_TEST_ACTIVATE_SIM', 'False') #Set this to true to force Sim activation on the console if Status is found to be "ready" instead of "active"
default_acT = os.environ.get('BENCHMARK_TEST_ACCESS_TECH', ACCESS_TECHNOLOGY_UMTS ) #Change this to the desired access technology

verbose = True
authKeyId = os.environ.get('SORACOM_AUTH_KEY_ID') 
authKey = os.environ.get('SORACOM_AUTH_KEY')
#not recommended to used username and password method. This is here only for testing
username = os.environ.get('SORACOM_USERNAME') 
password = os.environ.get('SORACOM_PASSWORD')

class Modem(object):

    def __init__(self, serial_port):
        self.port = serial_port
        self.last_value = None
        self.open()

    def open(self):
        self.ser = serial.Serial(port=serial_port, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
        self.send_command('ATE0\r\n',get_value=False)

    def close(self):
        self.ser.close()

    def send_command(self,command, get_value=True):
        self.ser.flushInput()
        self.ser.flushOutput()
        retVal = False
        if get_value:
            self.last_value = ''
        if verbose:
            print(command)
        self.ser.write(command.encode())
        data = self.ser.readlines()
        for line in data:
            if not line:
                continue        
            lineStr = line.decode()
            if lineStr=="\r\n":
                continue
            if verbose:
                print(lineStr)
            if lineStr.startswith('OK'):
                retVal = True
                break;
            elif lineStr.startswith('ERROR'):
                retVal = False
                break
            else:
                if get_value:
                    self.last_value = lineStr.strip()
        return retVal

    def get_last_value(self):
        return self.last_value
	
    def get_imsi(self):
        return self.send_command('AT+CIMI\r\n',get_value=True)
	
    def get_manufacturer(self):
        return self.send_command('AT+CGMI\r\n',get_value=True)

    def get_model(self):
        return self.send_command('AT+CGMM\r\n',get_value=True)

    def get_revision(self):
        return self.send_command('AT+CGMR\r\n',get_value=True)

    def get_serial_number(self):
        return self.send_command('AT+CGSN\r\n',get_value=True)
		
    def set_operation_mode(self, fun, rst=0):
        return self.send_command('AT+CFUN=%d, %d\r\n'%(fun,rst),get_value=False)

    def get_registration_status(self):
        return self.send_command('AT+CREG?\r\n',get_value=True)

    def get_network_status(self):
        return self.send_command('AT+COPS?\r\n',get_value=True)

    def get_signal_quality(self):
        return self.send_command('AT+CSQ\r\n',get_value=True)
		
    def get_reg_status_from_last_creg_value(self):
        if self.last_value != None:
            creg = self.last_value.strip()
            if creg.startswith("+CREG: "):
                comma_idx = creg.find(',')
                stat_str = creg[comma_idx+1:]
                comma_idx = stat_str.find(',')
                if comma_idx == -1:
                    return int (stat_str[0:].strip())
                else:
                    return int (stat_str[0:comma_idx].strip())
        return None

    def set_network_registration_auto(self, act=default_acT):
        retval = self.send_command('AT+COPS=0,2,"",%s\r\n'%act,get_value=False)
        return retval

    def activate_packet_data_context(self):
        retval = self.send_command('AT+CGDCONT=1,"IP","soracom.io"\r\n',get_value=False)
        retval = retval and self.send_command('AT+CGACT=1,1\r\n',get_value=False)
        return retval
        
    def get_packet_data_context_status(self):
        return self.send_command('AT+CGACT?\r\n',get_value=True)

    def get_packet_data_context_status_from_last_value(self):
        if self.last_value != None:
            cgact = self.last_value.strip()
            if cgact.startswith("+CGACT: "):
                comma_idx = cgact.find(',')
                stat_str = cgact[comma_idx+1:]
                comma_idx = stat_str.find(',')
                if comma_idx == -1:
                    return int (stat_str[0:])
                else:
                    return int (stat_str[0:comma_idx])
        return None
        
    def clear_sim_cache(self):
        #Clear Packet Switched Location information
        retval = self.send_command('AT+CRSM=214,28531,0 ,0,14,"FFFFFFFFFFFFFF92F5010000FF01"\r\n',get_value=False)
        #Clear Loci
        retval = retval and self.send_command('AT+CRSM=214,28542,0,0,11,"FFFFFFFF92F5010000FF01"\r\n',get_value=False)
        #Clear Fplmn
        retval = retval and self.send_command('AT+CRSM=214,28539,0,0,30,"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"\r\n',get_value=False)
        #Clear EF_Keys
        retval = retval and self.send_command('AT+CRSM=214,28424,0,0,33,"07FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"\r\n',get_value=False)
        #Clear EF_Keys_Packet_Switched
        retval = retval and self.send_command('AT+CRSM=214,28425,0,0,33,"07FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"\r\n',get_value=False)
        #Clear EF_NetPar
        retval = retval and self.send_command('AT+CRSM=214,28612,0,0,255,"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"\r\n',get_value=False)
        return retval

    def clear_modem_cache(self):
        #Facory defaults
        return self.send_command('AT&F\r\n',get_value=False)

        
class SoracomApiService(object):
    def __init__(self):
        self.operatorId = ''
        self.apiKey=''
        self.apiToken=''
        self.username=''
        self.password=''
        self.operatorId=''
        self.apiRoot='https://g.api.soracom.io/v1/'

    def get_auth_headers(self):
        return {'Content-type': 'application/json', 'Accept': 'application/json', 'X-Soracom-API-Key': self.apiKey, 'X-Soracom-Token': self.apiToken }
        
    def auth(self, authKeyId, authKey):
        url = self.apiRoot + "auth"
        data = {'authKeyId': authKeyId, 'authKey': authKey}
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers)
        if r.status_code == 200:
            json_response  = r.json()
            self.apiKey = json_response['apiKey']
            self.operatorId = json_response['operatorId']
            self.apiToken = json_response['token']
        return r.status_code
		
    def authPassword(self, username, password):
        url = self.apiRoot + "auth"
        data = {'email': username, 'password': password}
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers)
        if r.status_code == 200:
            json_response  = r.json()
            self.apiKey = json_response['apiKey']
            self.operatorId = json_response['operatorId']
            self.apiToken = json_response['token']
        return r.status_code
		
    def get_subscriber(self, imsi):
        url = self.apiRoot + "subscribers/" + imsi
        r = requests.get(url, headers=self.get_auth_headers())
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def activate_subscriber(self, imsi):
        url = self.apiRoot + "subscribers/" + imsi + "/activate"
        r = requests.post(url, headers=self.get_auth_headers())
        return r.status_code


#Start
if verbose:
    print("# Starting!")

if authKeyId == None or authKey == None:
    if username == None or password == None:
        print("Missing environment var SORACOM_AUTH_KEY_ID or SORACOM_AUTH_KEY!")
        exit(-1)
	
m = Modem(serial_port)
api = SoracomApiService()

#SET OPERATION MODE : LOW POWER MODE [NOT SUPPORTED BY ALL MODEM]
#if verbose:
#    print("# Setting operation mode: low power mode")
#m.set_operation_mode(0)
#time.sleep(2)

#READ IMSI
if verbose:
    print("# Reading IMSI")
imsi = None
if m.get_imsi():
    imsi = m.last_value.strip()
else:
    print("Failed to retrieve the IMSI from modem!")
    exit(-1)

manufacturer=''
model=''
revision=''
serial_number=''

if m.get_manufacturer():
    manufacturer = m.last_value.strip()
if m.get_model():
    model = m.last_value.strip()
if m.get_revision():
    revision = m.last_value.strip()
if m.get_serial_number():
    serial_number = m.last_value.strip()
	
#QUERY SIM STATUS
if verbose:
    print("# Querying sim status")
if authKeyId == None or authKey == None:
    stat = api.authPassword(username,password)
else:
    stat = api.auth(authKeyId,authKey)

if stat== 200:
    subscriber = api.get_subscriber(imsi)
    if subscriber == None:
        print("Failed to retrieve the Subscriber data!")
        exit(-1)
else:
    print("Authentication failed with status code " +str(stat))
    exit(-1)

modTime = datetime.fromtimestamp(float(subscriber['lastModifiedAt'])/1000.0)
iccid = subscriber['iccid']
status = subscriber['status']
online = False
onlineTime = None
if subscriber['sessionStatus'] != None:
    online = subscriber['sessionStatus']['online']
    #if online:
        #onlineTime = datetime.fromtimestamp(float(subscriber['sessionStatus']['lastUpdatedAt'])/1000.0)

#STATUS
if verbose:
    print("# Status assessment")
#STATUS=OTHER
if status != "ready" and status != "active":
    print("Expected sim status ready or active. Was " +status)
    exit(-1)

#STATUS = READY, ACTIVATE SIM IF NECESSARY (option)
if status == "ready" and activate.lower()=="true":
    stat = api.activate_subscriber(imsi)
    if stat != 200:
        print("Failed to activate sim with status code " +stat)
        exit(-1)

#STATUS = ACTIVE
#CLEAR SIM CACHE
if verbose:
    print("# Clearing Sim Cache")
if not m.clear_sim_cache():
    print("Failed to clear sim cache!")
    exit(-1)

#CLEAR MODEM CACHE
if verbose:
    print("# Clearing modem cache. Please wait ...")
m.clear_modem_cache()
time.sleep(30)

#Connection is lost when reseting cache
m.close()
m = Modem(serial_port)

#SET OPERATION MODE: ONLINE MODE
if verbose:
    print("# Setting operation mode: online mode. Please wait ...")
m.set_operation_mode(1,1)
time.sleep(30)
#Sometimes Connection is lost when doing AT+CFUN
m.close()
m = Modem(serial_port)

#RECORD START TIME
startTime = datetime.now()
m.set_network_registration_auto()

#WAIT FOR CREG
if verbose:
    print("# Waiting for network registration")
creg_stat = 0
n = 0
while creg_stat != 1 and creg_stat != 5 :
    time.sleep(1)
    n = n + 1
    if m.get_registration_status():
        creg_stat = m.get_reg_status_from_last_creg_value()
    #Each 5 seconds if MT is not searching force the search
    if creg_stat == 0:
        print("# Modem is NOT currently searching network...")
        if (n%60) == 0:
            print("# Reseting functionality ...")
            m.set_operation_mode(1,0)
        elif (n%15 == 0):
            print("# Requesting automatic search ...")
            m.set_network_registration_auto()
    elif creg_stat == 1:
        print("# Modem is registered on home network...")
    elif creg_stat == 2:
        print("# Modem is currently searching network...")
    elif creg_stat == 3:
        print("# Registration denied...")
    elif creg_stat == 5:
        print("# Modem is registered on roaming network...")
    else:
        print("# Modem is in unknown registration state...")

cops=''
if m.get_network_status():
    cops = m.get_last_value()

csq=''
if m.get_signal_quality():
    csq = m.get_last_value()
	
#RECORD CREG TIME
cregTime = datetime.now()
if verbose:
    if creg_stat == 1:
        print("# Network registered : home network")
    else:
        print("# Network registered : roaming")

#CREATE PDP CONTEXT
if verbose:
    print("# Connecting to packet data")
m.activate_packet_data_context()
    
#WAIT FOR CGACT
#if verbose:
#    print("# Waiting for packet data context activation")
#cgact_stat = 0
#while cgact_stat != 1 :
#    time.sleep(1)
#    if not m.get_packet_data_context_status():
#        print("Failed to get packet data context activation!")
#        exit(-1)
#    cgact_stat = m.get_packet_data_context_status_from_last_value()

#RECORD CGACT TIME
#cgactTime = datetime.now()
#if verbose:
#    print("# PDP context activated")
m.close()

#WAIT FOR SIM STATUS CHANGE
if verbose:
    print("# Waiting for sim status to change. Please wait ...")
    
while not online:
    time.sleep(1)
    subscriber = api.get_subscriber(imsi)
    if subscriber == None:
        print("Failed to retrieve the Subscriber data!")
        exit(-1)
    if subscriber['sessionStatus'] != None:
        online = subscriber['sessionStatus']['online']
        #if online:
            #onlineTime = datetime.fromtimestamp(float(subscriber['sessionStatus']['lastUpdatedAt'])/1000.0)

#modTime = datetime.fromtimestamp(float(subscriber['lastModifiedAt'])/1000.0)
newStatus = subscriber['status']

#RECORD ONLINE TIME
onlineTime = datetime.now()

print("# -----------------BENCHMARK STATISTICS-----------------")

print("SIM ICCID %s IMSI %s"%(iccid,imsi))
print("Modem Manufacturer            : %s"%manufacturer)
print("Modem Model                   : %s"%model)
print("Modem Revision                : %s"%revision)
print("Modem Serial number           : %s"%serial_number)
print("Sim Status on console         : %s"%status)
print("Online                        : "+str(online))
print("Start time (after cache clear): "+str(startTime))
print("Network registered time       : "+str(cregTime))
#print("PDP context activated time   : "+str(cgactTime))
print("Console Online time           : "+str(onlineTime))
print("Time taken to register network: "+str(cregTime-startTime))
print("Time taken to come online     : "+str(onlineTime-startTime))
print("Network registered            : "+cops)
print("Signal quality                : "+csq)
print("# ------------------------------------------------------")
