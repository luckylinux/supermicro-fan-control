#!/bin/bash

# Determine SUPERMICRO_FAN_CONTROL_REPO_ROOT_PATH if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v SUPERMICRO_FAN_CONTROL_ROOT ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); SUPERMICRO_FAN_CONTROL_ROOT=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Change to current Working Directory
cd "${SUPERMICRO_FAN_CONTROL_ROOT}" || exit

# Active Virtual Environment
source venv/bin/activate

# Run Application
uvicorn app:app --host ${SUPERMICRO_FAN_CONTROL_HTTP_BIND_HOST:-127.0.0.1} --port ${SUPERMICRO_FAN_CONTROL_HTTP_BIND_PORT:-8080}
