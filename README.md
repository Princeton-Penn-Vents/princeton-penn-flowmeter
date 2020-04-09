# princeton-penn-flowmeter
Software for patent and nurse stations

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

```bash
git clone https://github.com/Princeton-Penn-Vents/princeton-penn-flowmeter
cd princeton-penn-flowmeter
sudo apt update
sudo apt upgrade
sudo apt install python3-pyqt5 python3-zmq # Required on the base system, included in NOOBs
sudo apt install vim # for my sanity for development
sudo python3 -m pip install pyqtgraph pyzmq
python3 -m pip install black pytest # Useful for development, skip for productoin
```
