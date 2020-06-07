#!/usr/bin/env python3


import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--name", default="data.out", help="Base filename to record to")
parser.add_argument("--file", help="DEPRECATED: do no use")
parser.add_argument(
    "--dir", help="Directory to record to (device_log will be appended)"
)
arg = parser.parse_args()

if arg.file:
    print("Warning: Do not use --file, use --dir and/or --name instead")

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
from typing import Optional, TextIO, Iterator, TYPE_CHECKING, Dict, Any
from contextlib import contextmanager, ExitStack

if TYPE_CHECKING:
    from typing_extensions import Final

DIR = Path(__file__).parent.resolve()

if arg.dir:
    directory = Path(arg.dir).expanduser().resolve() / "device_log"
else:
    directory = DIR / "device_log"

if arg.name:
    print("Logging to", directory)
    directory.mkdir(parents=True, exist_ok=True)

ReadoutHz: "Final" = 50.0
oversampleADC: "Final" = 4

NReadoutTemp: "Final" = 50 * oversampleADC
NReadout: "Final" = 0
nbytesPN: "Final" = 18
nbytesSF: "Final" = 9
nbytesTEMP: "Final" = 6
nbytesDP: "Final" = 3
hystTEMP: "Final" = 1.0  # change temperature is difference is higher than hystTemp
minTEMP: "Final" = 42.0
operTEMP: "Final" = 45.0
maxTEMP: "Final" = 48.0
dcSTEP: "Final" = 1
dcMAX: "Final" = 9000
dcRANGE: "Final" = 10000
dcSTROBE: "Final" = 1 * NReadoutTemp
pinPWM: "Final" = 13


def sgn(a: float) -> float:
    return (a > 0) - (a < 0)


chanMP3V5004: "Final" = 0

DEVICE_SDP3: "Final" = 0x21  # grounded ADDR pin


def getADC(spi: spidev.SpiDev, channel: int) -> int:
    # Check channel valid
    # if ((channel > 7) or (channel < 0)):
    #  return -1
    # Perform SPI (spiMCP3008.xfer2 keeps CS asserted)
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    # Reformat
    adcOut = ((r[1] & 0xF) << 8) + r[2]
    return adcOut


@contextmanager
def pi_cleanup() -> Iterator[pigpio.pi]:
    """
    This ensures that the π is closed, with the heater turned off, even if an error happens.
    """
    pi = pigpio.pi()
    try:
        yield pi
    finally:
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
            return open(str(new_file_path), "x")
        except FileExistsError:
            i += 1


def read_loop(
    spi: spidev.SpiDev,
    pi: pigpio.pi,
    hSDP3: "pigpio.Handle",
    running: threading.Event,
    myfile: Optional[TextIO],
):
    dcTEMP = 3500

    # first issue stop command
    pi.i2c_write_device(hSDP3, [0x3F, 0xF9])
    # read product number and serial number
    print("handle {}".format(hSDP3))

    time.sleep(0.5)

    pi.i2c_write_device(hSDP3, [0x36, 0x7C])
    pi.i2c_write_device(hSDP3, [0xE1, 0x02])
    dataSDP3 = pi.i2c_read_device(hSDP3, nbytesPN)
    bdataSDP3 = dataSDP3[1]
    pnmsw = int.from_bytes(bdataSDP3[0:2], byteorder="big", signed=False)
    pnlsw = int.from_bytes(bdataSDP3[3:5], byteorder="big", signed=False)
    pn = (pnmsw << 16) | pnlsw
    snmmsw = int.from_bytes(bdataSDP3[6:8], byteorder="big", signed=False)
    snmsw = int.from_bytes(bdataSDP3[9:11], byteorder="big", signed=False)
    snlsw = int.from_bytes(bdataSDP3[12:14], byteorder="big", signed=False)
    snllsw = int.from_bytes(bdataSDP3[15:17], byteorder="big", signed=False)
    sn = (snmmsw << 48) | (snmsw << 32) | (snlsw << 16) | snllsw
    print("pn", hex(pn), "sn", hex(sn))

    # start continuous readout with averaging with differential pressure temperature compensation
    pi.i2c_write_device(hSDP3, [0x36, 0x15])

    time.sleep(0.020)

    # get initial values of differential pressure, temperature and the differential pressure scale factor
    dataSDP3 = pi.i2c_read_device(hSDP3, nbytesSF)
    bdataSDP3 = dataSDP3[1]
    dp = int.from_bytes(bdataSDP3[0:2], byteorder="big", signed=True)
    temp = (bdataSDP3[3] << 8) | bdataSDP3[4]
    dpsf = float((bdataSDP3[6] << 8) | bdataSDP3[7])
    print("Time", time.time(), "dp", dp, "temp", temp, "dpsf", dpsf)

    curTEMP = temp / 200.0
    pi.set_PWM_range(pinPWM, dcRANGE)
    pi.set_PWM_dutycycle(pinPWM, dcTEMP)
    dcFREQ = pi.get_PWM_frequency(pinPWM)
    print(
        "time: {} dp / dpsf: {:.4f} temp: {:.4f}".format(
            time.time() * 1000, dp / dpsf, temp / 200.0
        )
    )
    print(
        "PWM settings: Range = {} Freq = {} Step = {} Strobe = {}".format(
            dcRANGE, dcFREQ, dcSTEP, dcSTROBE
        )
    )

    NReadout = 0
    ADCsamples = []

    last_errorTEMP = 1.0  # + sign helps with cold start
    first_crossTEMP = True
    dcTEMP_at_cross: int = 0

    for _ in frequency(1.0 / (ReadoutHz * oversampleADC), running):  # Readout in Hz

        NReadout += 1
        tmpADC = getADC(spi, chanMP3V5004)
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

        d = {"v": 1, "t": ts, "P": ADCavg, "F": tmpdp}  # type: Dict[str, Any]

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

            d.update({"C": curTEMP, "D": dcTEMP, "sn": sn})

            if myfile is not None:
                d["file"] = myfile.name

        ds = json.dumps(d)
        pub_socket.send_string(ds)

        if myfile is not None:
            print(ds, file=myfile)


with ExitStack() as stack:

    pi = stack.enter_context(pi_cleanup())
    spiMCP3008 = stack.enter_context(spidev.SpiDev())
    ctx = stack.enter_context(zmq.Context())
    pub_socket = stack.enter_context(ctx.socket(zmq.PUB))

    pub_socket.bind("tcp://*:5556")

    myfile = None  # type: Optional[TextIO]

    if arg.name:
        file_path = directory / arg.name
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

    spiMCP3008.open(0, 0)
    spiMCP3008.max_speed_hz = 1350000  # 500000

    while not running.is_set():
        # Get I2C bus handle
        hSDP3 = pi.i2c_open(1, DEVICE_SDP3)
        try:
            read_loop(spiMCP3008, pi, hSDP3, running, myfile)
        except pigpio.error:
            # 1 second of "fake" readings
            for i in range(int(ReadoutHz)):
                d = {"v": 1, "t": int(1000 * time.monotonic())}  # type: Dict[str, Any]
                if i == 0 and myfile is not None:
                    d["file"] = myfile.name

                pub_socket.send_json(d)

                running.wait(1 / ReadoutHz)
                if running.is_set():
                    break
        finally:
            pi.i2c_close(hSDP3)
