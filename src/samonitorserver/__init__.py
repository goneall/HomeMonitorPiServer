'''
Main server script - continuously polls for alarm signals on the 
Raspberry PI GPIO and sends a message to the Android app through
Google GCM.

Parameters: Pushover app token (required), Pushover user key (required), MQTT broker user (required), MQTT broker password (required)
'''

import shelve, time, sys, urllib, http.client, logging, socket
from raspberrysupport import raspberrymonitor
from paho.mqtt import client as mqtt_client

class RelayServerException(Exception): pass

storage_file_name = 'samonitordata'
log_file_name = '/var/log/samonitor/samonitor.log'
wave_file_name = '/etc/samonitor/doorbell.wav'

# log_file_name = 'samonitor.log'
savedata = shelve.open(storage_file_name)
wait_time_for_alarm_reset = 10.0
alarm_poll_wait_time = 0.4
max_errors = 100

# MQTT constants
broker = '10.0.0.104'
port = 1883
topic = "samonitor"
client_id = 'alarm-pi-034a3fd5-5907-46fd-a3fc-430e949de802'

logging.basicConfig(filename=log_file_name,level=logging.INFO,format='%(asctime)s %(message)s')

raspberry_monitor = raspberrymonitor.RaspberryMonitor()

pushover_app_token = sys.argv[1]
pushover_user_key = sys.argv[2]
mqtt_user = sys.argv[3]
mqtt_password = sys.argv[4]

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.log(logging.INFO,"Connected to MQTT Broker!")
        else:
            logging.log(logging.ERROR,"Failed to connect, return code %d\n".format(rc))
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id = client_id, protocol = mqtt_client.MQTTv5, transport = "tcp")

    # client.username_pw_set(username, password)
    client.username_pw_set(username = mqtt_user, password = mqtt_password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

def on_disconnect(client, userdata, rc):
    print("Disconnected with result code")
    print(rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.log(logging.INFO,'Disconnected from MQTT - reconnecting...')
        time.sleep(reconnect_delay)
        try:
            client.reconnect()
            logging.log(logging.INFO, "Reconnected successfully!")
            return
        except Exception as err:
            logging.log(logging.ERROR, "%s. Reconnect failed. Retrying...".format(err))

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.log(logging.ERROR, "Reconnect failed after %s attempts. Exiting...")

client = connect_mqtt()
client.on_disconnect = on_disconnect
    
def sendMessageToAndroid(msg):
    # Sends a message to Andorid device
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
            urllib.parse.urlencode({
                "token": pushover_app_token,
                "user": pushover_user_key,
                "message": msg
            }), { "Content-type": "application/x-www-form-urlencoded" })
    response = conn.getresponse()
    if response.status != 200:
        logging.log(logging.ERROR, "Error returned from Pushover")
        logging.log(logging.ERROR, response.reason)

def sendMessageToMqtt(sub_topic, msg):
    result = client.publish(topic + "/" + sub_topic, msg)
    status = result[0]
    if status != 0:
        logging.log(logging.ERROR, 'Failed to send message to MQTT')
    
def alarm():
    # Alarm has been tripped
    sendMessageToAndroid('Home Alarm Tripped')
    sendMessageToMqtt('alarm_tripped', 'Home alarm tripped')
    logging.log(logging.INFO, 'Alarm tripped message sent')
    
def alarm_reset():
    # Alarm has been tripped
    sendMessageToAndroid('Alarm reset')
    sendMessageToMqtt('alarm_reset', 'Home alarm reset')
    logging.log(logging.INFO, 'Alarm reset message sent')
    
def started():
    # Monitor has been (re)started
    sendMessageToAndroid('SA Monitor Started')
    sendMessageToMqtt('started', 'SA Monitor Started')
    logging.log(logging.INFO, 'Starting SA Monitor')
    
def doorbell():
#    raspberry_monitor.playwave(wave_file_name)
    sendMessageToAndroid('Doorbell pressed')
    sendMessageToMqtt('doorbell', 'Dorbell pressed');
    logging.log(logging.INFO, 'Doorbell')

# main loop
started()
alarmtripped = False
doorbellpressed = False
numerrors = 0   # Number of errors before a successful send message

try:
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
                    print("Error trying to send alarm:"+ e)
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
                    print ("Error trying to reset alarm:"+e)
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
                    print("Error trying to ring doorbell:"+e)
                    numerrors = numerrors + 1
                    if numerrors > max_errors:
                        break
                doorbellpressed = True
        else:
            if doorbellpressed:
                doorbellpressed = False
        time.sleep(alarm_poll_wait_time)
except Exception as e:
    print("Unhandled exception: "+e)
    logging.log(logging.ERROR, 'Unhandled exception' + e)
finally:
    sendMessageToMqtt('ending', 'SA Monitor shutting down')
    sendMessageToAndroid('SA Monitor shutting down')
