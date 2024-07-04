#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing ${scriptpath}/${relativepath}); fi

# Load functions
source ${toolpath}/functions.sh

# Define Paths
SUPERMICRO_FAN_CONTROL_CONFIG_PATH="/etc/supermicro-fan-control"

# Create Folders
mkdir -p "${SUPERMICRO_FAN_CONTROL_CONFIG_PATH}"
mkdir -p /opt/supermicro-fan-control

# Create TMP Folder (only needed for Binary Files built using Nuitka --onefile)
mkdir -p /opt/supermicro-fan-control/tmp


if [ ! -f "/etc/modules-load.d/beep.conf" ]
then
   # Rebuild initramfs
   REBUILD_INITRD="yes"
else
   # Do NOT rebuild initramfs
   REBUILD_INITRD="no"
fi

# Upgrade existing Files if Any
# !! The new Extension used is .yml instead of .yaml !!
mapfile -t oldconfigfiles < <( find "${SUPERMICRO_FAN_CONTROL_CONFIG_PATH}" -iname *.yaml* )

for oldconfigfile in "${oldconfigfiles[@]}"
do
   # Rename Extension using BASH
   #newconfigfile=${oldconfigfile/".yaml"/".yml"}

   # Rename Extension using SED
   # At the end of the File
   newconfigfile=$(echo "${oldconfigfile}" | sed -E "s|(.*?)\.yaml$|\1.yml|g")

   # In the middle of the File
   newconfigfile=$(echo "${newconfigfile}" | sed -E "s|(.*?)\.yaml\.(.*?)$|\1.yml.\2|g")

   # Echo
   echo "Renaming ${oldconfigfile} to ${newconfigfile}"

   # Perform Operation
   mv "${oldconfigfile}" "${newconfigfile}"
done

exit 9

# Setup Kernel Module loading for BEEP
echo "pcspkr" > /etc/modules-load.d/beep.conf

# Revert "ugly and loud noise, getting on everyone's nerves; this should be done by a nice pulseaudio bing (Ubuntu: #77010)"
# This was apparently introduced by Ubuntu, but I believe it's better to know than NOT to know, when we have a critical issue !
sed -Ei "s|^blacklist pcspkr|#blacklist pcspkr|" /etc/modprobe.d/blacklist.conf

# Echo
#echo "IMPORTANT: Remember to Update / Regenerate your initramfs/initrd in case this is the first Time you execute this Script"
#echo "IMPORTANT: This is/might be required to properly load the pcspkr / BEEP Kernel Module"

if [[ "REBUILD_INITRD" == "yes" ]]
then
   # Rebuild initramfs
   if [[ -n $(command -v update-initramfs) ]]
   then
      # Debian/Ubuntu/etc
      echo "Rebuild INITRD using update-initramfs"
      update-initramfs -k all -u
   elif [[ -n $(command -v dracut) ]]
   then
      # Fedora/RHEL/Archlinux/etc
      echo "Rebuild INITRD using dracut"
      dracut --regenerate-all --force
   else
      # Other
      echo "!! YOU MUST MANUALLY REBUILD INITRD. NEITHER update-initramfs NEITHER dracut have been detected !!"
   fi
fi

# Create venv
python3 -m venv /opt/supermicro-fan-control/venv

# Activate venv
source /opt/supermicro-fan-control/venv/bin/activate

# Enable Development Tools
if [[ "${ENABLE_DEVEL}" == "yes" ]]
then
    pip install -r requirements.devel.txt
fi

# If NOT in Manual Debug Mode
if [[ "${DEBUG_MODE}" == "yes" ]]
then
    # Install Requirements (Suppress Echo)
    pip install -q -r requirements.prod.txt
else
    # Install Requirements (Echo)
    pip install -r requirements.prod.txt
fi

# Install App
cp -r opt/supermicro-fan-control/* /opt/supermicro-fan-control/

# Ensure Proper Permissions
chmod 755 /opt/supermicro-fan-control/bin/supermicro-fan-control.py

# Install Example Settings
cp -r etc/supermicro-fan-control/* "${SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/"

# Install Systemd Service
cp etc/systemd/system/supermicro-fan-control.service /etc/systemd/system/supermicro-fan-control.service

# Reload Systemd Daemon (at least to suppress warnings)
systemctl daemon-reload

# If NOT in Manual Debug Mode
if [[ "${DEBUG_MODE}" != "yes" ]]
then
    # Enable Service
    systemctl enable supermicro-fan-control.service

    # Restart Service
    systemctl restart supermicro-fan-control.service

    # Show Status of Service in case the are any Errors
    systemctl status --no-pager supermicro-fan-control.service

    # Show and Follow Logs
    journalctl -f -xeu supermicro-fan-control.service
fi
