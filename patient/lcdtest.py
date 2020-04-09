#!/usr/bin/env python3

# LCD display - I2C handled by pigpio.pi()
import sys
import time
import signal
import pigpio

# ------------------
# output file setup
# ------------------
#outputFileName = 'patient.dat'
#f = open(outputFileName,'w')
#sys.stdout = f
# ------------------
# output file end of setup
# ------------------
# ------------------
# LCD display setup
# ------------------
DEVICE_LCD = 0x3C # Slave 0x78 << 1
# Get pigio connection
pi = pigpio.pi()
# Get I2C bus handle
hLCD = pi.i2c_open(6,DEVICE_LCD)
# initialize
time.sleep(0.04) # wait 40ms
pi.i2c_write_device(hLCD,[0x00,0x38]) # Function set - 8 bit, 2 line, norm height, inst table 0
time.sleep(0.01) # wait 10ms
pi.i2c_write_device(hLCD,[0x00,0x39]) # Function set - 8 bit, 2 line, norm height, inst table 1
time.sleep(0.01) # wait 10ms
pi.i2c_write_device(hLCD,[0x00,0x14]) # Set bias 1/5
pi.i2c_write_device(hLCD,[0x00,0x78]) # Set contrast low
pi.i2c_write_device(hLCD,[0x00,0x5E]) # ICON display, Booster on, Contrast high
time.sleep(0.3) # wait 300ms
pi.i2c_write_device(hLCD,[0x00,0x6D]) # Font on, Amp ratio 6
time.sleep(0.3) # wait 300ms
pi.i2c_write_device(hLCD,[0x00,0x0C]) # Display on, Cursor off, Cursor Pos off
pi.i2c_write_device(hLCD,[0x00,0x01]) # Clear display
time.sleep(0.002) # wait 2ms
pi.i2c_write_device(hLCD,[0x00,0x06]) # Entry mode increment

# Set line 1 6th position
pi.i2c_write_device(hLCD,[0x00,0x86])
# Write line 1
pi.i2c_write_device(hLCD,[0x40,0x48,0x45,0x4c,0x4c,0x4f])
# Set line 2 6th position
pi.i2c_write_device(hLCD,[0x00,0xC6])
# Write line 2
pi.i2c_write_device(hLCD,[0x40,0x57,0x4f,0x52,0x4c,0x44,0x21])

pi.i2c_close(hLCD)
pi.stop()
