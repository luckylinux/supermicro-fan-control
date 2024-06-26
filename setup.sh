#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing ${scriptpath}/${relativepath}); fi

# Create Folders
mkdir -p /etc/supermicro-fan-control
mkdir -p /opt/supermicro-fan-control

# Create venv
python3 -m venv /opt/supermicro-fan-control/venv

# Activate venv
source /opt/supermicro-fan-control/venv/bin/activate

# Install Requirements
pip install -r requirements.txt

# Install App
cp -r opt/supermicro-fan-control/* /opt/supermicro-fan-control/

# Ensure Proper Permissions
chmod 755 /opt/supermicro-fan-control/bin/supermicro-fan-control.py

# Install Example Settings
cp -r etc/supermicro-fan-control/* /etc/supermicro-fan-control/

# Install Systemd Service
cp etc/systemd/system/supermicro-fan-control.service /etc/systemd/system/supermicro-fan-control.service

# If NOT in Manual Debug Mode
if [[ "${DEBUG_MODE}" == "yes" ]]
then
    # Reload Systemd Daemon
    systemctl daemon-reload

    # Enable Service
    systemctl enable supermicro-fan-control.service

    # Restart Service
    systemctl restart supermicro-fan-control.service

    # Show Status of Service in case the are any Errors
    systemctl status supermicro-fan-control.service
fi