'''
Main server script - continuously polls for alarm signals on the 
Raspberry PI GPIO and sends a message to the Android app through
Google GCM.

Parameters: GCMServerKey (required), IP Address of relay server (optional), Port number of relay server (optional)
'''

import shelve, time, sys, urllib2, logging, socket
import gcmclient
from raspberrysupport import raspberrymonitor

class RelayServerException(Exception): pass

extra_home_monitor_url = "com.sourceauditor.sahomemonitor.homemonitorurl"
extra_home_monitor_audio_url = "com.sourceauditor.sahomemonitor.homemonitoraudiourl"
extra_message_from_home = "com.sourceauditor.sahomemonitor.messagefromhome"
storage_file_name = 'samonitordata'
log_file_name = '/var/log/samonitor/samonitor.log'
wave_file_name = '/etc/samonitor/doorbell.wav'
# log_file_name = 'samonitor.log'
savedata = shelve.open(storage_file_name)
default_registration_ids = ['APA91bHJzeHJUUL4jQ_cWsxk-Dc2cnnbdfecxrp7RAmq3r-EwdJ2QekokUbIg4Zc5Aw_2QPt_IYQrzA7XhNJyls8u9RPvXN-rJr9PWoPhXEt22jOMN3ZtpXxqg8pmhLgwUVEGKkpMq0vMJ8r8Y8WQ-_7vBRzaDrJzitPZkeC20it2clmvCPczvQ']
key_registration_ids = 'registration_ids'
key_last_exception = 'lastexception'
wait_time_for_alarm_reset = 10.0
alarm_poll_wait_time = 0.4
max_errors = 100
ipecho_url = 'http://ipecho.net/plain'
server_port = '8081'
audio_port = '8000'
audio_mountpoint = 'webcam'
cached_public_ip = ""
public_ip_update_time = 1.0      # last time the public IP was updated
time_to_refresh_public_ip = 1000 # number of seconds to wait before updating the public IP address

logging.basicConfig(filename=log_file_name,level=logging.INFO,format='%(asctime)s %(message)s')

raspberry_monitor = raspberrymonitor.RaspberryMonitor()

use_relay = False
saServerGcm = None
relayClient = None
relay_ip_address = '10.0.0.7'
relay_port = 13373
ip_reflector_port = 13374

server_key = sys.argv[1]
if len(sys.argv) > 2:
    use_relay = True
    relay_ip_address = sys.argv[2]
if len(sys.argv) > 3:
    relay_port = sys.argv[3]
if use_relay:
    import gcmrelay.relayclient
    relayClient = gcmrelay.relayclient.GcmRelayClient(relay_ip_address, relay_port, server_key)
if not use_relay:
    saServerGcm = gcmclient.GCM(server_key)

def getMyPublicIp():
    global public_ip_update_time
    global cached_public_ip
    now = time.time()
    time_since_last_update = now - public_ip_update_time
    time_expired = time_since_last_update > time_to_refresh_public_ip
    if time_expired or cached_public_ip == "":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((relay_ip_address, ip_reflector_port))
        s.send('getIP')
        cached_public_ip = s.recv(1024)
        s.close()
    return cached_public_ip
    
def getServerUrl():
    retval = 'http://' + getMyPublicIp() + ':' + server_port
    return retval

def getAudioUrl():
    retval = 'http://' + getMyPublicIp() + ':' + audio_port + '/' + audio_mountpoint
    return retval

def sendMessageToAndroid(msg):
    # Sends a message to Andorid device
    data = {extra_home_monitor_url: getServerUrl(), 
            extra_home_monitor_audio_url: getAudioUrl(),
            extra_message_from_home: msg}

    if not savedata.has_key(key_registration_ids):
        savedata[key_registration_ids] = default_registration_ids
        savedata.sync()
        
    reg_ids = savedata[key_registration_ids]
    if (use_relay):
        response = relayClient.send(registration_ids=reg_ids, data=data)
    else:
        response = saServerGcm.json_request(registration_ids=reg_ids, data=data)
    if 'exception' in response:
        raise RelayServerException(response['exception'])
    if 'errors' in response:
        for error, reg_ids in response['errors'].items():
            # Check for errors and act accordingly
            if error is 'NotRegistered':
                # Remove reg_ids from database
                for reg_id in reg_ids:
                    savedata[key_registration_ids].remove(reg_id)
    if 'canonical' in response:
        for reg_id, canonical_id in response['canonical'].items():
            # Replace reg_id with canonical_id in your database
            new_reg_ids = savedata[key_registration_ids]
            new_reg_ids.remove(reg_id)
            new_reg_ids.append(canonical_id)
            savedata[key_registration_ids] = new_reg_ids
            
            savedata.sync()

    
def alarm():
    # Alarm has been tripped
    sendMessageToAndroid('Home Alarm Tripped')
    logging.log(logging.INFO, 'Alarm tripped message sent')
    
def alarm_reset():
    # Alarm has been tripped
    sendMessageToAndroid('Alarm reset')
    logging.log(logging.INFO, 'Alarm reset message sent')
    
def started():
    # Monitor has been (re)started
    sendMessageToAndroid('SA Monitor Started')
    logging.log(logging.INFO, 'Starting SA Monitor')
    
def doorbell():
#    raspberry_monitor.playwave(wave_file_name)
    sendMessageToAndroid('Doorbell')
    logging.log(logging.INFO, 'Doorbell')

# main loop
started()
alarmtripped = False
doorbellpressed = False
numerrors = 0   # Number of errors before a successful send message
while True:
    if raspberry_monitor.is_alarm_on():
        if alarmtripped:
            time.sleep(wait_time_for_alarm_reset)
        else:
            try:
                alarm()
                numerrors = 0
            except Exception as e:
                savedata[key_last_exception] = e
                savedata.sync()
                print "Error trying to send alarm:", e
                numerrors = numerrors + 1
                if numerrors > max_errors:
                    break
            alarmtripped = True
    else:   # alarm is not on
        if alarmtripped:
            try:
                alarm_reset()
                numerrors = 0
            except Exception as e:
                savedata[key_last_exception] = e
                print "Error trying to reset alarm:", e
                numerrors = numerrors + 1
                if numerrors > max_errors:
                    break
            alarmtripped = False
    if raspberry_monitor.is_doorbell_on():
        if not doorbellpressed:
            try:
                doorbell()
            except Exception as e:
                savedata[key_last_exception] = e
                print "Error trying to ring doorbell:", e
                numerrors = numerrors + 1
                if numerrors > max_errors:
                    break
            doorbellpressed = True
    else:
        if doorbellpressed:
            doorbellpressed = False
    time.sleep(alarm_poll_wait_time)