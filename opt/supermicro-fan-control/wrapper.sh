#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v SUPERMICRO_FAN_CONTROL_ROOT ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); SUPERMICRO_FAN_CONTROL_ROOT=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Change to current Working Directory
cd "${SUPERMICRO_FAN_CONTROL_ROOT}" || exit

# Active Virtual Environment
source venv/bin/activate

# Execute Python Application
python3 app/supermicro-fan-control.py "$@"
