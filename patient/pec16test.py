#!/usr/bin/env python3

# initially putting all hardware in one main program, then we can make it modular
# hardware interfaces:
# PEC16 rotary - interrupts and levels handled by pigpio.pi()
# LCD display - I2C handled by smbus.SMBus(I2CbusLCD)
# RGB backlight display - levels handled by pigpio.pi()
import sys
import time
import signal
import pigpio

# ------------------
# output file setup
# ------------------
# outputFileName = "patient.dat"
# f = open(outputFileName, "w")
# sys.stdout = f
# ------------------
# output file end of setup
# ------------------
# ------------------
# PEC16 rotary setup
# ------------------
# alarm threshold
alarmThreshold1 = 0  # initially zero (should be set to nominal value)
setThreshold1 = False  # initially False
# setup pins and interrupt handler for rotary knob (PEC16)
pinA = 17  # terminal A
pinB = 27  # terminal B
pinSW = 22  # switch
glitchFilter1 = 1  # 1 ms
glitchFilter10 = 10  # 10 ms
pi = pigpio.pi()
pi.set_mode(pinA, pigpio.INPUT)
pi.set_pull_up_down(pinA, pigpio.PUD_UP)
pi.set_glitch_filter(pinA, glitchFilter1)
pi.set_mode(pinB, pigpio.INPUT)
pi.set_pull_up_down(pinB, pigpio.PUD_UP)
pi.set_glitch_filter(pinB, glitchFilter1)
pi.set_mode(pinSW, pigpio.INPUT)
pi.set_pull_up_down(pinSW, pigpio.PUD_UP)
pi.set_glitch_filter(pinSW, glitchFilter10)
# rotaryA callback
def rotaryA_callback(ch, level, tick):
    global alarmThreshold1, setThreshold1
    if ch == pinA:
        if setThreshold1:
            levelB = pi.read(pinB)
            if levelB:
                alarmThreshold1 += 1  # ClockWise
            else:
                alarmThreshold1 -= 1  # CounterClockWise
            print(alarmThreshold1)


# rotarySW callback
def rotarySW_callback(ch, level, tick):
    global alarmThreshold1, setThreshold1
    if ch == pinSW:
        setThreshold1 = not setThreshold1
        print(setThreshold1)


pi.callback(pinA, pigpio.FALLING_EDGE, rotaryA_callback)
pi.callback(pinSW, pigpio.FALLING_EDGE, rotarySW_callback)
# ------------------
# PEC16 rotary end of setup
# ------------------
# ------------------
# LCD display setup
# ------------------
# check devices with sudo i2cdetect -y 1 (or -y <port>) makes a grid of addresses
# I2CbusLCD = 1
# Get I2C bus
# busLCD = smbus.SMBus(I2CbusLCD)
# DEVICE_LCD_Slave = 0x78
# busLCD.write_byte(DEVICE_LCD_Slave)
# Comsend = 0x00
# busLCD.write_byte(Comsend)
# busLCD.write_byte(0x38)
# time.sleep(0.01)
# busLCD.write_byte(0x39)
# time.sleep(0.01)
# busLCD.write_byte(0x14)
# busLCD.write_byte(0x78)
# busLCD.write_byte(0x5E)
# busLCD.write_byte(0x6D)
# busLCD.write_byte(0x0C)
# busLCD.write_byte(0x01)
# busLCD.write_byte(0x06)
# time.sleep(0.01)
# Datasend = 0x40
# vals = [
#    0b01001000,
#    0b01000101,
#    0b01001100,
#    0b01001100,
#    0b00100000,
#    0b01010111,
#    0b01001111,
#    0b01010010,
#    0b01001100,
#    0b01000100,
#    0b00100001,
# ]
# busLCD.write_i2c_block_data(DEVICE_LCD_Slave, Datasend, vals)
# ------------------
# LCD display end of setup
# ------------------
# ------------------
# RBG backlight display setup
# ------------------
# setup pins for RGB backlight
# pinR = 22  # Red
# pinG = 24  # Green
# pinB = 26  # Blue
# pi.set_mode(pinR, pigpio.OUTPUT)
# pi.set_pull_up_down(pinR, pigpio.PUD_UP)
# pi.set_mode(pinG, pigpio.OUTPUT)
# pi.set_pull_up_down(pinG, pigpio.PUD_UP)
# pi.set_mode(pinB, pigpio.OUTPUT)
# pi.set_pull_up_down(pinB, pigpio.PUD_UP)
# ------------------
# RBG backlight display end of setup
# ------------------

# event loop:
#    wait for rotary A or push button (pigpio interrupt handler)
#    update LCD display
while True:
    signal.pause()
    # time.sleep(1)  # 1 second
    # update display with alarmThreshold1 and setThreshold1 status