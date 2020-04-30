# princeton-penn-flowmeter
Software for patient and nurse stations for multi-patient ventilator
monitoring.

The hardware at the patient includes two sensors to measure flow and pressure
mounted on a flow block and equipped with a heating circuit to reduce condensation, 
a single board computer (SBC, in this case a Raspberry Pi model 4b/4GB), a 2x20 
character LCD display with RBG backlight, a rotary encoder and a piezo buzzer.
The sensor time series data from up to 20 patient boxes are transmitted to a nurse
monitoring station, where a graphical GUI presents an aggregate view of the
time series. The nurse monitoring station can either be an SBC or a more
standard laptop/desktop machine. Analysis code runs on both the patient box
and on the nurse monitoring station to derive quantities for both alarms
and display.

The software is written in Python and PyQt for portability.

# Installation

#### On a local machine:

```bash
git clone https://github.com/Princeton-Penn-Vents/princeton-penn-flowmeter
cd princeton-penn-flowmeter
conda env create
conda activate flowmeter
```

(and git pull, then conda env update to update)

### On a Raspberry Pi running Raspbian:

Boot up a fresh copy of Raspbian. At the setup screen, click next to proceed.
Select United States, American English, and New York for the country and
timezone settings. Set a password.  Check the box saying there's a black
border (there is one). You can select a network if you want to connect it
to the internet. Press "next" when asked about updating if you connected
to the internet. Press OK then restart.

Open the settings (Raspberry menu -> `Preferences` -> `Raspberry Pi Configuration`).
In the display tab, select "Disable" for `Screen Blanking`. Check the Interfaces tab to
see if there is anything you want to enable.

For a patient box, you need: I2C enabled, SPI enabled.  These are also set in config.txt.
Optional:  SSH enabled.

```bash
git clone https://github.com/Princeton-Penn-Vents/princeton-penn-flowmeter
cd princeton-penn-flowmeter
sudo apt update
sudo apt upgrade
sudo apt install python3-pyqt5 python3-zmq # Required on the base system, included in NOOBs
sudo apt-install python3-scipy
sudo apt install vim                       # For development, skip for production
sudo python3 -m pip install pyqtgraph pyzmq confuse
python3 -m pip install black pytest mypy   # Useful for development, skip for production
```


```bash
cd princeton-penn-flowmeter
sudo cp config/config.txt /boot/config.txt
sudo cp config/patientdevice.service /lib/systemd/system
sudo cp config/patientloop.service /lib/systemd/system
sudo systemctl enable pigpiod
sudo systemctl enable patientdevice
sudo systemctl enable patientloop
```
Now, you have all the code and automatic startup setup.
On reboot, all patient processes will be launched automatically.

<details><summary>Additional information: (click to expand)</summary>

To operate patient box manually:

To execute the readout, click on a terminal icon, then in the shell:

```
cd princeton-penn-flowmeter
./stopall
python3 ./device_loop.py —-file test.out
```

This will start printing temperature settings every second to the screen - will thermalize at 40C with the temperature servo,
and it will be recording pressure (in ADC counts from 0 to 4095) and flow rate (signed integer 0 to 32,767) and the time in milliseconds (with a precision of microseconds).  The RPi4 does not operate a clock when powered down, but rather begins from where it left off when shutdown.

You can `^C` at any time and look at the data. This will print it to the screen:

```bash
cat test0000.out
```
where the 0000 will increment every time the process is restarted through a local directory scan.
Logging of data is by default in ./device_log/

Operation of the LCD display and rotary and to serve data to the nurseguii from the device_loop, one can run locally:

```
cd princeton-penn-flowmeter
python3 ./patient_loop.py
```

For `/boot/config.txt`:  These lines change:

```
dtparam=i2c_arm=on,baudrate=200000
dtparam=spi=on
```

These lines are added:

```
dtoverlay=i2c1,pins_2_3
dtoverlay=i2c6,pins_22_23
```

#### pigpio cleanup, if needed:

```bash
sudo killall pigpiod
```

</details>

---

## Common test procedures:

#### Replay a log file

```bash
# Terminal 1
./device_json_to_socket.py data/20200422_helmet.out

# Terminal 2
./patientgui.py

# Terminal 3
./nursegui.py --debug -n 4 --port 8100
```

---

# Acknowledgements

This project is supported by Princeton University and by NSF Cooperative Agreement OAC-1836650.
