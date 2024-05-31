'''
Main server script - continuously polls for alarm signals on the 
Raspberry PI GPIO and sends a message to the Android app through
Google GCM.

Parameters: Pushover app token (required), Pushover user key (required)
'''

import time, sys, urllib, httplib, logging
from datetime import datetime
from raspberrysupport import raspberrymonitor

log_file_name = '/var/log/samonitor/samonitor.log'
wave_file_name = '/etc/samonitor/doorbell.wav'

wait_time_for_alarm_reset = 10.0
alarm_poll_wait_time = 0.3 
max_errors = 100

logging.basicConfig(filename=log_file_name,level=logging.INFO,format='%(asctime)s %(message)s')

raspberry_monitor = raspberrymonitor.RaspberryMonitor()

pushover_app_token = sys.argv[1]
pushover_user_key = sys.argv[2]

def sendMessageToAndroid(msg):
    # Sends a message to Andorid device
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
            urllib.urlencode({
                "token": pushover_app_token,
                "user": pushover_user_key,
                "message": msg
            }), { "Content-type": "application/x-www-form-urlencoded" })
    response = conn.getresponse()
    if response.status != 200:
        logging.log(logging.ERROR, "Error returned from Pushover")
        logging.log(logging.ERROR, response.reason)

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
    sendMessageToAndroid('Doorbell')
    raspberry_monitor.playwave(wave_file_name)
    logging.log(logging.INFO, 'Doorbell')

# main loop
alarmtripped = False
doorbellpressed = False
numerrors = 0   # Number of errors before a successful send message

try:
    started()
    while True:
        if raspberry_monitor.is_alarm_on():
            if alarmtripped:
                time.sleep(wait_time_for_alarm_reset)
            else:
                try:
                    alarm()
                    numerrors = 0
                except Exception as e:
                    logging.log(logging.ERROR, "Error trying to send to alarm: "+str(e))
                    print("Error trying to send alarm:"+ str(e))
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
                    logging.log(logging.ERROR, "Error trying to reset alarm: "+str(e))
                    print ("Error trying to reset alarm:"+str(e))
                    numerrors = numerrors + 1
                    if numerrors > max_errors:
                        break
                alarmtripped = False
        if raspberry_monitor.is_doorbell_on():
            if not doorbellpressed:
                try:
                    doorbell()
                except Exception as e:
                    logging.log(logging.ERROR, "Error trying to ring doorbell: "+str(e))
                    print("Error trying to ring doorbell:"+str(e))
                    numerrors = numerrors + 1
                    if numerrors > max_errors:
                        break
                doorbellpressed = True
        else:
            if doorbellpressed:
                doorbellpressed = False
        time.sleep(alarm_poll_wait_time)
except Exception as e:
    print("Unhandled exception: "+str(e))
    logging.log(logging.ERROR, 'Unhandled exception' + str(e))
finally:
    sendMessageToAndroid('SA Monitor shutting down')
