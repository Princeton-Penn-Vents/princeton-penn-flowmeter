#!/usr/bin/env python3

# initially putting all hardware in one main program, then we can make it modular
# hardware interfaces:
# PEC16 rotary - interrupts and levels handled by pigpio.pi()
# LCD display - I2C handled by smbus.SMBus(I2CbusLCD)
# RGB backlight display - levels handled by pigpio.pi()
# MCP3008 ADC readings - SPI handled by spidel.SpiDev()
# SDP3 diff pressure sensor - I2C handled by smbus.SMBus(I2CbusSDP3)
# TIP-32 heating - PWM handled by pigpio.pi()
# MCP9808 temperature - I2C handled by smbus.SMBus(I2CbusMCP9808)
import sys
import time
import signal

# pigpio requires:
# sudo apt-get update (before install, if needed)
# sudo apt-get install pigpio python-pigpio python3-pigpio (install once)
# sudo pigpiod (on each boot)
# sudo killall pigpiod (for cleanup, if needed)
import pigpio

# smbus requires:
# sudo raspi-config -> Advanced Settings -> I2C Enable
# or manually sudo vi /etc/modprobe.d/raspi-blacklist.conf
# the underlying device is the i2c-bcm2708 (comment out blacklist)
# sudo apt-get install i2c-tools
# sudo install python-smbus
import smbus

# spidev requires:
# sudo raspi-config -> Advanced Settings -> SPI Enable
# lsmod | grep spi (check that spidev and spi_bcm2708 are running)
# spidev is there by default
import spidev

# ------------------
# output file setup
# ------------------
outputFileName = "patient.dat"
f = open(outputFileName, "w")
sys.stdout = f
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
pinA = 29  # terminal A
pinB = 31  # terminal B
pinSW = 21  # switch
glitchFilter1 = 1  # 1 ms
glitchFilter10 = 10  # 10 ms
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
    global alarmThreshold1, setThreshold1
    if ch == pinA:
        if setThreshold1:
            levelB = pi.read(pinB)
            if levelB:
                alarmThreshold1 += 1  # ClockWise
            else:
                alarmThreshold1 -= 1  # CounterClockWise


# rotarySW callback
def rotarySW_callback(ch, level, tick):
    global alarmThreshold1, setThreshold1
    if ch == pinSW:
        setThreshold1 = not setThreshold1


pi.callback(pinA, pigpio.FALLING_EDGE, rotaryA_callback)
pi.callback(pinSW, pigpio.FALLING_EDGE, rotarySW_callback)
# ------------------
# PEC16 rotary end of setup
# ------------------
# ------------------
# LCD display setup
# ------------------
# check devices with sudo i2cdetect -y 1 (or -y <port>) makes a grid of addresses
I2CbusLCD = 1
# Get I2C bus
busLCD = smbus.SMBus(I2CbusLCD)
DEVICE_LCD_Slave = 0x78
busLCD.write_byte(DEVICE_LCD_Slave)
Comsend = 0x00
busLCD.write_byte(Comsend)
busLCD.write_byte(0x38)
time.sleep(0.01)
busLCD.write_byte(0x39)
time.sleep(0.01)
busLCD.write_byte(0x14)
busLCD.write_byte(0x78)
busLCD.write_byte(0x5E)
busLCD.write_byte(0x6D)
busLCD.write_byte(0x0C)
busLCD.write_byte(0x01)
busLCD.write_byte(0x06)
time.sleep(0.01)
Datasend = 0x40
vals = [
    0b01001000,
    0b01000101,
    0b01001100,
    0b01001100,
    0b00100000,
    0b01010111,
    0b01001111,
    0b01010010,
    0b01001100,
    0b01000100,
    0b00100001,
]
busLCD.write_i2c_block_data(DEVICE_LCD_Slave, Datasend, vals)
# ------------------
# LCD display end of setup
# ------------------
# ------------------
# RBG backlight display setup
# ------------------
# setup pins for RGB backlight
pinR = 22  # Red
pinG = 24  # Green
pinB = 26  # Blue
pi.set_mode(pinR, pigpio.OUTPUT)
pi.set_pull_up_down(pinR, pigpio.PUD_UP)
pi.set_mode(pinG, pigpio.OUTPUT)
pi.set_pull_up_down(pinG, pigpio.PUD_UP)
pi.set_mode(pinB, pigpio.OUTPUT)
pi.set_pull_up_down(pinB, pigpio.PUD_UP)
# ------------------
# RBG backlight display end of setup
# ------------------
# ------------------
# MCP3008 ADC setup
# ------------------
# Establish SPI device on Bus 6, Device 0
spiMCP3008 = spidev.SpiDev()
spiMCP3008.open(6, 0)
spiMCP3008.max_speed_hz = 500000
chanMP3V5004 = 0  # channel 0


def getAdc(channel):
    # Check channel valid
    # if ((channel > 7) or (channel < 0)):
    #  return -1
    # Perform SPI (spi.xfer2 keeps CS asserted)
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    # Reformat
    adcOut = ((r[1] & 3) << 8) + r[2]
    return adcOut


# ------------------
# MCP3008 ADC end of setup
# ------------------
# ------------------
# SDP3 diff pressure sensor setup
# ------------------
I2CbusSDP3 = 1
# Get I2C bus
busSDP3 = smbus.SMBus(I2CbusSDP3)
DEVICE_SDP3 = 0x21  # grounded ADDR pin
# read product identifier 0x367C 32-bits and last 8 are revision number (SDP32: 0x03010201)
# PN[31:24], PN[23:16],CRC,PN[15:8],PN[7:0],CRC
# read serial number 0xE102 64-bits
# PN[31:24], PN[23:16],CRC,PN[15:8],PN[7:0],CRC,SN[63:56],SN[55:48],CRC,SN[47:40],SN[39:32],CRC,SN[31:24],SN[23:16],CRC,SN[15:8],SN[7:0],CRC
# Differential pressure Average till read  0x3615 16-bit command
busSPD3.write_i2c_block_data(DEVICE_SDP3, 0x3F, [0x15])
# first measurement available after 8ms
# read is 9 consecutive bytes (scale factor for differential pressure in Pa)
# DPMSB,DPLSB,CRC,TEMPMSB,TMPLSB,CRC,SFMSB,SFLSB,CRC
# read can stop after 3 bytes, if temp and pressure scale factor are not needed
nbytes = 9
dataSDP3 = busSDP3.read_i2c_black_data(DEVICE_SDP3, 0, nbytes)
temp = (tmpdataSDP3[3] << 8) + tmpdataSDP3[4]
dpsf = (tmpdataSDP3[6] << 8) + tmpdataSDP3[7]
# stop continuous measurement 0x3FF9
# busSPD3.write_i2c_block_data(DEVICE_SDP3, 0x3F, [0xF9])
# for soft reset, DEVICE_RESET = 0x00 and command 0x0006 (20ms reset)
# sdp3 interrupt handler
def sdps3_handler(signum, frame):
    global dpsf
    ts = time.time()
    nb = 3
    tmpdataSDP3 = busSDP3.read_i2c_black_data(DEVICE_SDP3, 0, nbytes)  # read SDP3
    tmpdp = ((tmpdataSDP3[0] << 8) + tmpdataSDP3[1]) * dpsf
    tmpADC = getADC(chanMP3V5004)
    print(ts, tmpdp, tmpADC)


signal.signal(signal.SIGALRM, sdp3_handler)
signal.setitimer(signal.ITIMER_REAL, 1, 0.01)  # 10Hz of readout
# ------------------
# SDP3 diff pressure sensor end of setup
# ------------------

# event loop:
#    wait for rotary A or push button (pigpio interrupt handler)
#    wait for readout of diff pressure sensor and pressure sensor (signal interrupt handler)
#    update LCD display
while True:
    time.sleep(1)  # 1 second
    # update display with alarmThreshold1 and setThreshold1 status
