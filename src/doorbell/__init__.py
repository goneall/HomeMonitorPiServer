'''
Script to just monitor for the doorbell - continuously polls for alarm signals on the 
Raspberry PI GPIO and plays a wav file if the doorbell is detected
'''

import time
from raspberrysupport import raspberrymonitor

wave_file_name = '/etc/samonitor/doorbell.wav'
alarm_poll_wait_time = 0.2
max_errors = 100
raspberry_monitor = raspberrymonitor.RaspberryMonitor()

    
def doorbell():
    raspberry_monitor.playwave(wave_file_name)

# main loop
doorbellpressed = False
numerrors = 0   # Number of errors before a successful send message
while True:
    if raspberry_monitor.is_doorbell_on():
        if not doorbellpressed:
            try:
                doorbell()
            except Exception as e:
                print "Error trying to ring doorbell:", e
                numerrors = numerrors + 1
                if numerrors > max_errors:
                    break
            doorbellpressed = True
    else:
        if doorbellpressed:
            doorbellpressed = False
    time.sleep(alarm_poll_wait_time)