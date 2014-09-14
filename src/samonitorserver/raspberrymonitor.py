'''
Monitors the Raspberry Pi and reports the status of any alarms
Created on Sep 9, 2014

@author: Gary O'Neall
'''

import RPi.GPIO as GPIO

alarm_pin = 17

class RaspberryMonitor(object):
    
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(alarm_pin, GPIO.IN)
    def is_alarm_on(self):
        retval = (GPIO.input(alarm_pin) == True)
        return retval
