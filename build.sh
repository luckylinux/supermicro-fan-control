#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing ${scriptpath}/${relativepath}); fi

# Enable Developer Tools
ENABLE_DEVEL="yes"

# Run Setup
source ${toolpath}/setup.sh

# Activate VENV
source /opt/supermicro-fan-control/venv/bin/activate

# Create Folders
mkdir -p build
mkdir -p dist
mkdir -p tmp
mkdir -p dist-onefile

# Copy Sources
cp ${toolpath}/opt/supermicro-fan-control/bin/supermicro-fan-control.py ${toolpath}/tmp/supermicro-fan-control.py

# Change Directory to tmp Folder
cd ${toolpath}/tmp || exit

# Build using Nuitka
python -m nuitka --standalone --follow-imports --onefile supermicro-fan-control.py


# Build using Nuitka (needed in order to bypass some noexec Permission Issues ?)
# https://github.com/Nuitka/Nuitka/issues/2246
#python -m nuitka --standalone --follow-imports --onefile --onefile-tempdir-spec=/opt/supermicro-fan-control/tmp supermicro-fan-control.py

# Move into the Respective Folders
mv supermicro-fan-control.dist/* ${toolpath}/dist/
mv supermicro-fan-control.build/* ${toolpath}/build/
mv supermicro-fan-control.bin ${toolpath}/dist-onefile/

# Remove Temporary Folders
rm -rf supermicro-fan-control.dist
rm -rf supermicro-fan-control.build
rm -rf supermicro-fan-control.onefile-build

