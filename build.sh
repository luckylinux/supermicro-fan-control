#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing ${scriptpath}/${relativepath}); fi

# Build Root
buildroot="${toolpath}/build"

# Dist Root
distroot="${toolpath}/dist"

# Create venv
python3 -m venv "${toolpath}/venv"

# Activate venv
source "${toolpath}/venv/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install & Upgrade Development Tools
pip install -r requirements.devel.txt
pip install --upgrade -r requirements.devel.txt

# Install Requirements (Echo)
pip install -r requirements.prod.txt

# Create Folders
mkdir -p ${buildroot}
mkdir -p ${distroot}
mkdir -p ${buildroot}/build
mkdir -p ${distroot}/dist
mkdir -p ${distroot}/dist-onefile

# Copy Sources
cp "${toolpath}/opt/supermicro-fan-control/bin/supermicro-fan-control.py" "${buildroot}/supermicro-fan-control.py"

# Change Directory to tmp Folder
cd "${buildroot}" || exit

# Build using Nuitka
python -m nuitka --standalone --follow-imports --onefile supermicro-fan-control.py

# Build using Nuitka (needed in order to bypass some noexec Permission Issues ?)
# https://github.com/Nuitka/Nuitka/issues/2246
#python -m nuitka --standalone --follow-imports --onefile --onefile-tempdir-spec=/opt/supermicro-fan-control/tmp supermicro-fan-control.py

# Move into the Respective Folders
mv supermicro-fan-control.dist/* "${distroot}/dist/"
mv supermicro-fan-control.build/* "${buildroot}/build/"
mv supermicro-fan-control.bin "${distroot}/dist-onefile/"

# Remove Temporary Folders
rm -rf "supermicro-fan-control.dist"
rm -rf "supermicro-fan-control.build"
rm -rf "supermicro-fan-control.onefile-build"
