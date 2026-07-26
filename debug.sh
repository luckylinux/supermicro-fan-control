#!/bin/bash

# Determine SUPERMICRO_FAN_CONTROL_REPO_ROOT_PATH if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v SUPERMICRO_FAN_CONTROL_REPO_ROOT_PATH ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); SUPERMICRO_FAN_CONTROL_REPO_ROOT_PATH=$(realpath --canonicalize-missing ${scriptpath}/${relativepath}); fi

# We ARE in DEBUG Mode using this Script
# Make sure we pass this Information to setup.sh
DEBUG_MODE="yes"

# Run Setup
source ${SUPERMICRO_FAN_CONTROL_REPO_ROOT_PATH}/setup.sh

# If in Manual Debug Mode
if [[ "${DEBUG_MODE}" == "yes" ]]
    then
    # Stop Systemd Service
    systemctl stop supermicro-fan-control.service

    # Status Systemd Service
    systemctl status supermicro-fan-control.service
fi

# Run the Application Directly to Debug
/opt/supermicro-fan-control/bin/supermicro-fan-control.py
