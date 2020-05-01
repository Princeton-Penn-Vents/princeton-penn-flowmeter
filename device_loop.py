#!/usr/bin/env python3


import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--file", help="File to record to")
arg = parser.parse_args()

# hardware interfaces:
# SDP3 diff pressure sensor - I2C handled by pigpio.pi()
# MCP3008 ADC readings - SPI handled by spidev.SpiDev()

import time
import signal
import pigpio
import spidev
import json
import zmq
import threading
from pathlib import Path
from typing import Optional, TextIO, Iterator
from contextlib import contextmanager, ExitStack

DIR = Path(__file__).parent.resolve()
(DIR.parent / "device_log").mkdir(exist_ok=True)

ReadoutHz = 50.0
oversampleADC = 4
ADCsamples = []

NReadoutTemp = 50 * oversampleADC
NReadout = 0
nbytesPN = 18
nbytesSF = 9
nbytesTEMP = 6
nbytesDP = 3
hystTEMP = 1.0  # change temperature is difference is higher than hystTemp
minTEMP = 37.0
operTEMP = 40.0
maxTEMP = 43.0
dcSTEP = 1
dcTEMP = 3000
dcMAX = 9000
dcRANGE = 10000
dcSTROBE = 1 * NReadoutTemp
sgn = lambda a: (a > 0) - (a < 0)
first_crossTEMP = True
dcTEMP_at_cross = 0
last_errorTEMP = 0.0
pinPWM = 13


# ------------------
# MCP3008 ADC setup
# ------------------
# Establish SPI device on Bus 0, Device 0
spiMCP3008 = spidev.SpiDev()
spiMCP3008.open(0, 0)
spiMCP3008.max_speed_hz = 1350000  # 500000
chanMP3V5004 = 0


def getADC(channel: int) -> int:
    # Check channel valid
    # if ((channel > 7) or (channel < 0)):
    #  return -1
    # Perform SPI (spiMCP3008.xfer2 keeps CS asserted)
    r = spiMCP3008.xfer2([1, (8 + channel) << 4, 0])
    # Reformat
    adcOut = ((r[1] & 0xF) << 8) + r[2]
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
if not pi.connected:
    exit()
# Get I2C bus handle
hSDP3 = pi.i2c_open(1, DEVICE_SDP3)
# first issue stop command
pi.i2c_write_device(hSDP3, [0x3F, 0xF9])
# read product number and serial number
print("handle {}".format(hSDP3))

time.sleep(0.5)

pi.i2c_write_device(hSDP3, [0x36, 0x7C])
pi.i2c_write_device(hSDP3, [0xE1, 0x02])
dataSDP3 = pi.i2c_read_device(hSDP3, nbytesPN)
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


time.sleep(0.020)

# get initial values of differential pressure, temperature and the differential pressure scale factor
dataSDP3 = pi.i2c_read_device(hSDP3, nbytesSF)
# print(dataSDP3)
bdataSDP3 = dataSDP3[1]
dp = int.from_bytes(bdataSDP3[0:2], byteorder="big", signed=True)
# print(int.from_bytes(bdataSDP3[3:5], byteorder='big', signed=False))
# print(int.from_bytes(bdataSDP3[6:8], byteorder='big', signed=False))
# dp = (bdataSDP3[0] << 8) | bdataSDP3[1]
temp = (bdataSDP3[3] << 8) | bdataSDP3[4]
dpsf = float((bdataSDP3[6] << 8) | bdataSDP3[7])
print(time.time(), dp, temp, dpsf)

curTEMP = temp / 200.0
pi.set_PWM_range(pinPWM, dcRANGE)
pi.set_PWM_dutycycle(pinPWM, dcTEMP)
dcFREQ = pi.get_PWM_frequency(pinPWM)
print("{} {:.4f} {:.4f}".format(time.time() * 1000, dp / dpsf, temp / 200.0))
print(
    "PWM settings: Range = {} Freq = {} Step = {} Strobe = {}".format(
        dcRANGE, dcFREQ, dcSTEP, dcSTROBE
    )
)


@contextmanager
def pi_cleanup() -> Iterator[None]:
    """
    This ensures that the π is closed, with the heater turned off, even if an error happens.
    """
    try:
        yield
    finally:
        pi.i2c_close(hSDP3)
        pi.set_PWM_dutycycle(pinPWM, 0)
        pi.stop()


def frequency(length: float, event: threading.Event) -> Iterator[None]:
    """
    This pauses as long as needed after running
    """
    while not event.is_set():
        start_time = time.monotonic()
        yield
        diff = time.monotonic() - start_time
        left = length - diff
        if left > 0:
            event.wait(left)


def open_next(mypath: Path) -> TextIO:
    """
    Open the next available file
    """
    i = 0
    while True:
        try:
            name = "{n}{i:04}{s}".format(n=mypath.stem, i=i, s=mypath.suffix)
            new_file_path = mypath.with_name(name)
            return open(new_file_path, "x")
        except FileExistsError:
            i += 1


with pi_cleanup(), ExitStack() as stack, zmq.Context() as ctx, ctx.socket(
    zmq.PUB
) as pub_socket:
    pub_socket.bind("tcp://*:5556")

    myfile = None  # type: Optional[TextIO]

    if arg.file:
        file_path = Path(arg.file)
        myfile = stack.enter_context(open_next(file_path))
        print("Logging:", myfile.name)

    running = threading.Event()

    def close(_number, _frame):
        print("Closing down server...")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        running.set()

    signal.signal(signal.SIGINT, close)
    signal.signal(signal.SIGTERM, close)

    for _ in frequency(1.0 / (ReadoutHz * oversampleADC), running):  # Readout in Hz

        NReadout += 1
        tmpADC = getADC(chanMP3V5004)
        ADCsamples.append(tmpADC)

        # Continue if we are currently in oversampling
        if (NReadout % oversampleADC) != 0:
            continue

        ADCavg = 0.0
        if len(ADCsamples):
            ADCavg = sum(ADCsamples) / len(ADCsamples)
        ADCsamples = []

        ts = int(1000 * time.monotonic())

        if (NReadout % NReadoutTemp) == 0:
            nbytes = nbytesTEMP
        else:
            nbytes = nbytesDP

        tmpdataSDP3 = pi.i2c_read_device(hSDP3, nbytes)
        btmpdataSDP3 = tmpdataSDP3[1]
        tmpdp = int.from_bytes(btmpdataSDP3[0:2], byteorder="big", signed=True)

        d = {"v": 1, "t": ts, "P": ADCavg, "F": tmpdp}

        if len(btmpdataSDP3) == nbytesTEMP:
            tmptemp = ((btmpdataSDP3[3] << 8) | btmpdataSDP3[4]) / 200.0
            print(ts, tmptemp, dcTEMP)
            if (NReadout % dcSTROBE) == 0:
                # Take-back-half algorithm
                errorTEMP = operTEMP - curTEMP
                if sgn(errorTEMP) != sgn(last_errorTEMP):
                    if first_crossTEMP:
                        first_crossTEMP = False
                    else:
                        dcTEMP = (dcTEMP + dcTEMP_at_cross) // 2
                    dcTEMP_at_cross = dcTEMP
                last_errorTEMP = errorTEMP

                # Standard servo (loop gain response)
                deltatemp = tmptemp - curTEMP
                if (deltatemp < hystTEMP / 10.0) and (curTEMP < minTEMP):
                    dcTEMP += dcSTEP
                    dcTEMP = min(dcMAX, dcTEMP)
                if ((curTEMP > operTEMP) and (deltatemp > hystTEMP / 20.0)) or (
                    curTEMP > maxTEMP
                ):
                    dcTEMP -= dcSTEP
                    dcTEMP = max(0, dcTEMP)
                pi.set_PWM_dutycycle(pinPWM, dcTEMP)

            curTEMP = tmptemp

            d.update({"C": curTEMP, "D": dcTEMP})

        ds = json.dumps(d)
        pub_socket.send_string(ds)

        if myfile is not None:
            print(ds, file=myfile)
