'''
Script to just monitor for the doorbell - continuously polls for alarm signals on the 
Raspberry PI GPIO and plays a wav file if the doorbell is detected
'''

import time
import samonitorserver

wave_file_name = '/etc/samonitor/doorbell.wav'
alarm_poll_wait_time = 1.0
max_errors = 100
raspberry_monitor = samonitorserver.raspberrymonitor.RaspberryMonitor()

    
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