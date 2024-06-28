# supermicro-fan-control
Supermicro Fan Control

# Introduction
This Project features two separate Components:
- Fan Speed Control (AKA "Variable Fan Speed")
- Device Overtemperature Protection (in case Cooling failed or airflow/static Pressure is not Sufficient to properly cool down Components)

For a Protection-Only (Overtemperature Protection) see my Separate [Cooling Failure Protection](https://github.com/luckylinux/cooling-failure-protection) Project.

**IMPORTANT**: it is **HIGHLY RECCOMENDED** to setup the Separate [Cooling Failure Protection](https://github.com/luckylinux/cooling-failure-protection) Service as well, in order to ensure some Level of Redundancy !!!

# Features
- Temperature Controller for Supermicro IPMI Devices ("Variable Fan Speed")
- Temperature Warning (BEEP) when System Cooling cannot keep up with Devices Temperatures
- Temperature Protection (SHUTDOWN) when System Cooling cannot keep up with Devices Temperatures

# Requirements
At the moment this was developed for use with GNU/Linux.

Nevertheless, since the Packages are very similar for both GNU/Linux and other UNIX-Like OS (TrueNAS, FreeBSD, etc), there shouldn't be a huge effort required in order to make the Tool Multi-Platform.

Feel free to Describe the required Changes in an Issue and/or submit a PR :+1:.

In order to run a (mostly) Automated Setup (using `setup.sh`) the Following is Required:
- `bash`

In order to be able to Run Correctly, the Tool needs the following Components/Systems:
- `python` Version 3 (Tested with `python` Version 3.11 and 3.12)
- `systemd` (in the future other Init Systems might be supported)
- `ipmitool` (to be able to change Fan Speed)
- `smartctl` (to read Disks Temperatures)
- `beep` (for generating an Audible WARNING generation in case Temperature is getting dangerously High)

# Installation
Clone the Repository:
```
git clone https://github.com/luckylinux/supermicro-fan-control.git
```

Change Folder to the Project that was just cloned:
```
cd supermicro-fan-control
```

Run the Setup:
```
./setup.sh
```

# Enable the Beep Module for early Warnings
Load the Kernel Module:
```
sudo modprobe pcspkr
```

Then perform a Test with:
```
beep -f 2500 -l 2000 -r 5 -D 1000
```

Set the Kernel Module to be automatically loaded at Startup:
```
echo "pcspkr" > /etc/modules-load.d/beep.conf
```

# Credits
Project based on the work of [Benjamin Bryan](https://b3n.org).

See his Blog Post for the [Original Code](https://b3n.org/supermicro-fan-speed-script/).

# References
- https://b3n.org/supermicro-fan-speed-script/
- https://forums.servethehome.com/index.php?threads/supermicro-x9-x10-x11-fan-speed-control.10059/page-10
- https://forums.servethehome.com/index.php?resources/supermicro-x9-x10-x11-fan-speed-control.20/
- https://unix.stackexchange.com/questions/65595/how-to-know-if-a-disk-is-an-ssd-or-an-hdd
- https://unix.stackexchange.com/questions/387855/make-lsblk-list-devices-by-id
