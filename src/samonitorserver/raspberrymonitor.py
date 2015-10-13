'''
Monitors the Raspberry Pi and reports the status of any alarms
Created on Sep 9, 2014

@author: Gary O'Neall
'''

import RPi.GPIO as GPIO
import pygame

alarm_pin = 17
doorbell_pin = 18

class RaspberryMonitor(object):

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(alarm_pin, GPIO.IN)
        GPIO.setup(doorbell_pin, GPIO.IN)
    def is_alarm_on(self):
        retval = (GPIO.input(alarm_pin) == True)
        return retval
    def is_doorbell_on(self):
        retval = (GPIO.input(doorbell_pin) == True)
        return retval
    def playwave(self, wavefile):
        pygame.mixer.init()
        pygame.mixer.music.load(wavefile)
        pygame.mixer.music.play()