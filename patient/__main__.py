#!/usr/bin/env python3


import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--file", help="File to record to")
arg = parser.parse_args()

# hardware interfaces:
# SDP3 diff pressure sensor - I2C handled by pigpio.pi()
# MCP3008 ADC readings - SPI handled by spidev.SpiDev()
import sys
import time
import signal
import pigpio
import binascii
import spidev
import json
import zmq
import atexit
import threading
import typing
import numpy as np

# ------------------
# output file setup
# ------------------
context = zmq.Context()
socket = context.socket(zmq.PUB)  # publish (broadcast)
socket.bind("tcp://*:5556")
ReadoutHz = 50.0
oversampleADC = 16
ADCsamples = []
NReadoutTemp = 50 * oversampleADC
NReadout = 0
nbytesPN = 18
nbytesSF = 9
nbytesTEMP = 6
nbytesDP = 3
# outputFileName = "patient.dat"
# f = open(outputFileName, "w")
# sys.stdout = f
# ------------------
# output file end of setup
# ------------------


# ------------------
# MCP3008 ADC setup
# ------------------
# Establish SPI device on Bus 0, Device 0
spiMCP3008 = spidev.SpiDev()
spiMCP3008.open(0, 0)
spiMCP3008.max_speed_hz = 1350000 # 500000
chanMP3V5004 = 0


def getADC(channel):
    # Check channel valid
    # if ((channel > 7) or (channel < 0)):
    #  return -1
    # Perform SPI (spiMCP3008.xfer2 keeps CS asserted)
    r = spiMCP3008.xfer2([1, (8 + channel) << 4, 0])
    # Reformat
    adcOut = ((r[1] & 3) << 8) + r[2]
    return adcOut


# ------------------
# MCP3008 ADC end of setup
# ------------------
# ------------------
# SDP3 diff pressure sensor setup
# ------------------
DEVICE_SDP3 = 0x21  # grounded ADDR pin
# Get pigio connection
pi = pigpio.pi()
# Get I2C bus handle
hSDP3 = pi.i2c_open(1, DEVICE_SDP3)
# first issue stop command
pi.i2c_write_device(hSDP3, [0x3F, 0xF9])
# read product number and serial number
print("handle {}".format(hSDP3))
pi.i2c_write_device(hSDP3, [0x36, 0x7C])
pi.i2c_write_device(hSDP3, [0xE1, 0x02])
nbytes = nbytesPN
dataSDP3 = pi.i2c_read_device(hSDP3, nbytes)
# print(dataSDP3)
bdataSDP3 = dataSDP3[1]
# print(binascii.hexlify(bdataSDP3[0:2]))
# print(binascii.hexlify(bdataSDP3[3:5]))
pnmsw = int.from_bytes(bdataSDP3[0:2], byteorder="big", signed=False)
pnlsw = int.from_bytes(bdataSDP3[3:5], byteorder="big", signed=False)
pn = (pnmsw << 16) | pnlsw
# print(binascii.hexlify(bdataSDP3[6:8]))
# print(binascii.hexlify(bdataSDP3[9:11]))
# print(binascii.hexlify(bdataSDP3[12:14]))
# print(binascii.hexlify(bdataSDP3[15:17]))
snmmsw = int.from_bytes(bdataSDP3[6:8], byteorder="big", signed=False)
snmsw = int.from_bytes(bdataSDP3[9:11], byteorder="big", signed=False)
snlsw = int.from_bytes(bdataSDP3[12:14], byteorder="big", signed=False)
snllsw = int.from_bytes(bdataSDP3[15:17], byteorder="big", signed=False)
sn = (snmmsw << 48) | (snmsw << 32) | (snlsw << 16) | snllsw
print(hex(pn), hex(sn))

# start continuous readout with averaging with differential pressure temperature compensation
pi.i2c_write_device(hSDP3, [0x36, 0x15])

# get initial values of differential pressure, temperature and the differential pressure scale factor
time.sleep(0.020)
nbytes = nbytesSF
dataSDP3 = pi.i2c_read_device(hSDP3, nbytes)
# print(dataSDP3)
bdataSDP3 = dataSDP3[1]
dp = int.from_bytes(bdataSDP3[0:2], byteorder="big", signed=True)
# print(int.from_bytes(bdataSDP3[3:5], byteorder='big', signed=False))
# print(int.from_bytes(bdataSDP3[6:8], byteorder='big', signed=False))
# dp = (bdataSDP3[0] << 8) | bdataSDP3[1]
temp = (bdataSDP3[3] << 8) | bdataSDP3[4]
dpsf = (float)((bdataSDP3[6] << 8) | bdataSDP3[7])
print(time.time(), dp, temp, dpsf)
print(
    "{} {:.4f} {:.4f}".format(
        time.time() * 1000, (float)(dp / dpsf), (float)(temp / 200.0)
    )
)

myfile: typing.Optional[typing.TextIO]

if arg.file:
    myfile = open(arg.file, "a")
    atexit.register(myfile.close)
else:
    myfile = None

# sdp3 interrupt handler
def sdp3_handler(signum, frame):
    global NReadout, ADCsamples
    NReadout += 1
    tmpADC = getADC(chanMP3V5004)
    ADCsamples.append(tmpADC)
    if (NReadout % oversampleADC) == 0:
        ADCavg = np.mean(ADCsamples)
        ADCsamples = []
        ts = int(1000 * time.time())
        if (NReadout % NReadoutTemp) == 0:
            nbytes = nbytesTEMP
        else:
            nbytes = nbytesDP
        tmpdataSDP3 = dataSDP3 = pi.i2c_read_device(hSDP3, nbytes)
        btmpdataSDP3 = tmpdataSDP3[1]
        tmpdp = int.from_bytes(btmpdataSDP3[0:2], byteorder="big", signed=True)
        d = {"v": 1, "t": ts, "P": ADCavg, "F": tmpdp}
        if len(btmpdataSDP3) == nbytesTEMP:
            tmptemp = (btmpdataSDP3[3] << 8) | btmpdataSDP3[4]
            print(ts, tmptemp / 200.0)
        socket.send_json(d)

# sdp3 interrupt file handler
def sdp3_file_handler(signum, frame):
    global NReadout, ADCsamples
    NReadout += 1
    tmpADC = getADC(chanMP3V5004)
    ADCsamples.append(tmpADC)
    if (NReadout % oversampleADC) == 0:
        ADCavg = np.mean(ADCsamples)
        ADCsamples = []
        ts = int(1000 * time.time())
        if (NReadout % NReadoutTemp) == 0:
            nbytes = nbytesTEMP
        else:
            nbytes = nbytesDP
        tmpdataSDP3 = dataSDP3 = pi.i2c_read_device(hSDP3, nbytes)
        btmpdataSDP3 = tmpdataSDP3[1]
        tmpdp = int.from_bytes(btmpdataSDP3[0:2], byteorder="big", signed=True)
        d = {"v": 1, "t": ts, "P": ADCavg, "F": tmpdp}
        ds = json.dumps(d)
        print(ds, file=myfile)
        socket.send_string(ds)
        if len(btmpdataSDP3) == nbytesTEMP:
            tmptemp = (btmpdataSDP3[3] << 8) | btmpdataSDP3[4]
            print(ts, tmptemp / 200.0)


if myfile:
    signal.signal(signal.SIGALRM, sdp3_file_handler)
else:
    signal.signal(signal.SIGALRM, sdp3_handler)
signal.setitimer(
    signal.ITIMER_REAL, 1, 1.0 / (ReadoutHz * oversampleADC)
)  # Readout in Hz

# ------------------
# SDP3 diff pressure sensor end of setup
# ------------------

forever = threading.Event()


def signal_handler(signal, frame):
    print("You pressed Ctrl+C!")
    pi.i2c_close(hSDP3)
    pi.stop()
    forever.set()


signal.signal(signal.SIGINT, signal_handler)

# Read until quit
forever.wait()
