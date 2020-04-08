# princeton-penn-flowmeter
Software for patent and nurse stations

# Installation

#### On a local machine:

```bash
conda env create
```

(and conda env update to update)
 
### On a Raspberry Pi running Raspbian:
 
Boot up a fresh copy of Raspbian. At the setup screen, click next to procede.
Select United Statess, American English, and New Yorck for the country and
timezone settings. Set a password.  Check the box saying there's a black
border (there is one). You can select a network if you want to connect it
to the internet.

```bash
git clone https://github.com/Princeton-Penn-Vents/princeton-penn-flowmeter
cd princeton-penn-flowmeter
apt update
apt upgrade
apt install vim # for my sanity
python3 -m pip install pyqtgraph
```
