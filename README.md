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
```shell
git clone https://github.com/luckylinux/supermicro-fan-control.git
```

Change Folder to the Project that was just cloned:
```shell
cd supermicro-fan-control
```

## Preferred (use Python in venv)
Run the Setup:
```shell
./setup.sh
```

After that, check the logs:
```shell
journalctl -f -xeu supermicro-fan-control
```

## Manual (use Binary Packages)
You can grab a `onefile` Package built using `nuitka` from the Releases Section.

You however need to Manually setup everything else, including:
- `systemd` Service
- Configuration Files in `/etc/supermicro-fan-control`

# Build
## Build a Binary Package
From inside the checked out Repository Folder:
```shell
cd supermicro-fan-controller
```

Run:
```shell
./build.sh
```

# Environment Configuration Variables
The following Environment Configuration Variables can be set:
- `SUPERMICRO_FAN_CONTROL_CONFIG_PATH`: where all the YML Configuration Files are located (defaults to `/etc/supermicro-fan-control`)

# Enable the Beep Module for early Warnings
UPDATE: this is now performed automatically by `setup.sh`.

Load the Kernel Module:
```shell
sudo modprobe pcspkr
```

Then perform a Test with:
```shell
beep -f 2500 -l 2000 -r 5 -D 1000
```

Set the Kernel Module to be automatically loaded at Startup:
```shell
echo "pcspkr" > /etc/modules-load.d/beep.conf
```

For Ubuntu at least. you also need to REMOVE the blacklisting in `/etc/modprobe.d/blacklist.conf`:
```shell
# ugly and loud noise, getting on everyone's nerves; this should be done by a
# nice pulseaudio bing (Ubuntu: #77010)
#blacklist pcspkr
```



# Update initramfs / initrd.
UPDATE: this is currently performed automatically if `update-initramfs` or `dracut` are Detected.

Debian/Ubuntu uses `update-initramfs`, while Fedora/RHEL/Archlinux use `dracut`.

You can also do it manually.

For example on Debian/Ubuntu:
```shell
update-initramfs -k all -u ; update-grub
```

# Test that is works Correctly
Currently, the `default` Profile has been Tested on Supermicro X10SLM-F/X10SLL-F Motherboards.

You **ABSOLUTELY NEED** to check that the Registers are set correctly for **your** Motherboard.

Take a Look at the References Section for some Examples of different Registers Values (RAW Values to be used with `ipmitool`).

After you found what works for you, please submit a PR with your Particular Motherboard Profile.

This will be included in `etc/supermicro-fan-control/ipmi.d/<motherboard>.yml`.

# ToDo
No Timeline is currently defined.

## Get Current Fan Speed
IMPLEMENTED in commit 4b9f3c39250d2bc7d39f1af5a22c4336e4f87530.

```shell
ipmitool -c sensor | grep -Ei "^FAN|^MB-FAN|^BPN-FAN"
```

## Implement Support for Other Systems
Use `echo` to directly Control PWM Fans on non-IPMI System.

Target is at the Moment an ASUS x570 AMD Ryzen System.

Notes: https://bbs.archlinux.org/viewtopic.php?id=225349

## Docker Image
In theory, it should be possible to run this as a Docker Container.

This will however require ROOT Privileges or Setuid Bit set and/or `CAP_SYS_RAWIO`, since smartctl requires those.

## Notifications
In the Future better Notifications than just a `beep` might be supported.

The current Plan would be to leverage the existing Frameworks/Bridges, including:
- `mailrise` (`smtp` -> `apprise`), requires an MTA to be Configured on the System running this Tool (e.g.`postfix`)
- [Notifiers Providers](https://notifiers.readthedocs.io/en/latest/providers/index.html)

# Credits
Project based on the work of [Benjamin Bryan](https://b3n.org).

See his Blog Post for the [Original Code](https://b3n.org/supermicro-fan-speed-script/).

# References
Initial Code:
- https://b3n.org/supermicro-fan-speed-script/

Register Settings and Explanation:
- https://forums.servethehome.com/index.php?threads/supermicro-x9-x10-x11-fan-speed-control.10059/page-10
- https://forums.servethehome.com/index.php?resources/supermicro-x9-x10-x11-fan-speed-control.20/
- https://serverfault.com/questions/662526/fan-speeds-on-supermicro-system-via-ipmi

Other:
- https://unix.stackexchange.com/questions/65595/how-to-know-if-a-disk-is-an-ssd-or-an-hdd
- https://unix.stackexchange.com/questions/387855/make-lsblk-list-devices-by-id

