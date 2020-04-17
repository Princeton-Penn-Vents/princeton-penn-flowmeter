# princeton-penn-flowmeter
Software for patient and nurse stations for multi-patient ventilator
monitoring.

The hardware at the patient includes two sensors, a single board computer
(SBC, in this case a Raspberry Pi model 4b), a 20x2 LCD, a rotary encoder and
additional electronics to allow configuration of alarm parameters. The sensor
time series data from up to 20 patient boxes are transmitted to a nurse
monitoring station, where a graphical GUI presents an aggregate view of the
time series. The nurse monitoring station can either be an SBC or a more
standard laptop/desktop machine. Analysis code runs on both the patient box
and on the nurse monitoring station to derive quantities for both alarms
and display.

The software is written in Python and PyQt for portability.

# Installation

#### On a local machine:

```bash
conda env create
```

(and conda env update to update)

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

For a patient box, you need: I2C enabled, SPI enabled, GPIO enabled.



```bash
git clone https://github.com/Princeton-Penn-Vents/princeton-penn-flowmeter
cd princeton-penn-flowmeter
sudo apt update
sudo apt upgrade
sudo apt install python3-pyqt5 python3-zmq # Required on the base system, included in NOOBs
sudo apt-install python3-scipy
sudo apt install vim                       # For my sanity for development
sudo python3 -m pip install pyqtgraph pyzmq
python3 -m pip install black pytest mypy   # Useful for development, skip for production
```


---

## Patient box


Basic install instructions for a new RPi4:  Once you have the RPi4 with an HDMI screen, USB keyboard and mouse, plug in the power cord.
It will load an operating system install tool called NOOBs. You choose US keyboard from the pulldown
and click to install Raspbian. This will take ~1 hour to complete and runs on its own.

After it reboots, it will ask you to change root password.
You should also go into interfaces and enable ssh, spi, i2c.
You might reboot again.

The tough part will be to connect this on the wireless. I think eduroam should work - click on the upper left WiFi icon and login.

Then you need to do this once:

Click on a terminal icon and execute these commands (copy `config.txt` to the disk from the email - could use a memory stick).

```bash
sudo cp config.txt /boot/config.txt
sudo systemctl enable pigpiod
sudo apt-get update
sudo apt-get install python3-scipy
sudo apt-get install python3-numpy
python3 -m pip install pyyaml
sudo apt-get install python3-pyqt5
python3 -m pip install pyqtgraph
git clone https://github.com/princeton-penn-vents/princeton-penn-flowmeter
```
Now, you have all the code. I would reboot the RPi4 (this will start pigpiod).

To execute the readout, click on a terminal icon, then in the shell:

```
cd princeton-penn-flowmeter
python3 ./patient/__main__.py —-file data.out
```

This will start printing temperature settings every second to the screen - will thermalize at 40C with the temperature servo,
and it will be recording pressure (in ADC counts from 0 to 4095) and flow rate (in signed integer) and the time in milliseconds (with a precision of microseconds).

You can `^C` at any time and look at the data. This will print it to the screen:


```bash
cat data.out
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

---

<details><summary>Previous notes: (click to expand)</summary>

#### pigpio requires:

```bash
sudo apt-get update (before install, if needed)
sudo apt-get install pigpio python-pigpio python3-pigpio (install once)
sudo pigpiod (on each boot)
sudo killall pigpiod (for cleanup, if needed)
import pigpio
```

#### smbus requires:

```bash
# or manually sudo vi /etc/modprobe.d/raspi-blacklist.conf
# the underlying device is the i2c-bcm2708 (comment out blacklist)
sudo apt-get install i2c-tools
sudo install python-smbus
import smbus
```

#### spidev requires:

```bash
lsmod | grep spi (check that spidev and spi_bcm2708 are running)
spidev is there by default
```

</details>

---

# Acknowledgements

This project is supported by Princeton University and by NSF Cooperative Agreement OAC-1836650.
