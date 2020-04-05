#!/usr/bin/env python3

import sys
import time
import signal
# requires: 
# sudo apt-get update (before install, if needed)
# sudo apt-get install pigpio python-pigpio python3-pigpio (install once)
# sudo pigpiod (on each boot)
# sudo killall pigpiod (for cleanup, if needed)
import pigpio

# alarm threshold
alarmThreshold1 = 0 #initially zero (should be set to nominal value)
setThreshold1 = False #initially False
# setup pins and interrupt handler for rotary knob (PEC16)
pinA = 29 # terminal A
pinB = 31 # terminal B
pinSW = 21 # switch
glitchFilter1 = 1 #1 ms
glitchFilter10 = 10 #10 ms
pi = pigpio.pi()
pi.set_mode(pinA, pigpio.INPUT)
pi.set_pull_up_down(pinA, pigpio.PUD_UP)
pi.set_glitch_filter(pinA, glitchFilter1)
pi.set_mode(pinB, pigpio.INPUT)
pi.set_pull_up_down(pinB, pigpio.PUD_UP)
pi.set_glitch_filter(pinB, glitchFilter1)
pi.set_mode(sw, pigpio.INPUT)
pi.set_pull_up_down(pinSW, pigpio.PUD_UP)
pi.set_glitch_filter(pinSW, glitchFilter10)
# rotaryA callback
def rotaryA_callback(ch, level, tick):
  global alarmThreshold1,setThreshold1
  if ch == pinA:
    if (setThreshold1):
      levelB = pi.read(pinB)
      if (levelB):
        alarmThreshold1 += 1 # ClockWise
      else:
        alarmThreshold1 -= 1 # CounterClockWise
# rotarySW callback
def rotarySW_callback(ch, level, tick):
  global alarmThreshold1,setThreshold1
  if ch == pinSW:
    setThreshold1 = !setThreshold1
pi.callback(pinA, pigpio.FALLING_EDGE, rotaryA_callback)
pi.callback(pinSW, pigpio.FALLING_EDGE, rotarySW_callback)
# wait for rotary A or push button
while True:
  time.sleep(1) # 1 second
  # update display with alarmThreshold1 and setThreshold1 status

