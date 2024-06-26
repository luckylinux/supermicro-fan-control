#!/opt/supermicro-fan-control/venv/bin/python3

# Core Libraries
import os
import sys
import subprocess
import time
import syslog
import re

# Python Modules to interact with YAML Files
import yaml
from yaml.loader import SafeLoader

# Python Pretty Print Module
import pprint

# Python json Module
import json

# Python DiskInfo Module
from diskinfo import Disk, DiskInfo

# Define Configuration Dictionary
CONFIG = dict()

# Initialize minimum Fan Speed to 50%
current_fan_speed = 50               # [%] Current Fan Speed

# Init
def init():
    # Allow Function to modify CONFIG Global Variable
    global CONFIG

    # Initialize CONFIG as a Dictionary
    CONFIG = dict()

# Filter Drive
def filter_drive(path):
    # Initialize String
    drivepath = ""

    # Only keep the element NOT containing "wwn"
    for item in path:
        if "wwn" in item:
            pass
        else:
            drivepath = item

    # Return Result
    return drivepath

# Merge Configuration
# If a Key is defined in both config_a and config_b, the Value of config_b will override the Value of config_a
def merge_config(config_a , config_b):

    # Initialize config as config_a
    config = config_a.copy()
    #pprint.pprint(config)

    if config is not None:
        # Echo
        print(f"[INFO] merging config_a with config_b")

        # Iterate over Existing Config
        for key, value in config.items():
            # Print Key
            #print(key)

            # If the key also exists in config_b, then replace value
            if key in config_b:
                # Echo
                print(f"[DEBUG] Override Key {key} in config ({value} -> {config_b[key]})")

                # Override
                config[key] = config_b[key]

            # Get Data of the current Iteration
            #currentdata = data[l]

            # Iterate over currentdata
            #for item in currentdata:
            #print(item)

            #currentimages = currentdata[item]["images"]
            #for im in currentimages:
            #   # Debug
            #   print(im)
            #
            #   # Get Tags associated with the current Image
            #   tags = currentimages[im]
            #
            #   # Append to the list
            #   images.append(image)

        # Add new Keys that were only in config_b
        for key, value in config_b.items():
            # Echo
            print(f"[DEBUG] Add non-existing Key {key} in config ({config_b[key]})")

            # Set Key
            config[key] = value

    else:
        # Simply use config_b
        print(f"[WARNING] config_a was empty/none: config_b will override everything")
        config = config_b.copy()
    
    # Return Result
    return config.copy()

# Read Configuration File
def read_config(filepath):
    # Allow Function to modify CONFIG Global Variable
    global CONFIG

    #pprint.pprint(CONFIG)

    if os.path.exists(filepath):
        # Echo
        print(f"[INFO] Loading File {filepath}")

        with open(filepath, 'r') as f:
            # Open YAML File in Safe Mode
            list_data = list(yaml.load_all(f, Loader=SafeLoader))

            if list_data is not None and len(list_data) > 0:
                # Unpack the List
                data = list_data[0]

                # Print
                #pprint.pprint(data)

                # Merge Config
                CONFIG = merge_config(CONFIG , data)
            else:
                # Echo
                print(f"[WARNING] File {filepath} is empty")
    else:
        # Echo
        print(f"[WARNING] File {filepath} does NOT exist")

# Get the current HDD/SSD/NVME Temperature(s)
def get_drives_temperatures():
    # Initialize Array
    temps = []

    # Check all Disks
    di = DiskInfo()
    disks = di.get_disk_list(sorting=True)

    # Loop over Disks
    for d in disks:
        id = d.get_byid_path()
        filteredid = filter_drive(id)
        temp = d.get_temperature()

        # If it's a Physical Disk (i.e. it has a Valid Temperature)
        if temp is not None:
            # Echo
            print(f"Disk {filteredid} -> Temperature: {temp}°C")

            # Add to Array
            temps.append(temp)

    # Return Result
    return temps

# Get the current CPU Temperature(s)
def get_cpu_temperatures():
    temp_output = subprocess.check_output("ipmitool sdr type temperature", shell=True).decode()
    cpu_temp_lines = [line for line in temp_output.split("\n") if "CPU" in line and "degrees" in line]

    if cpu_temp_lines:
        cpu_temps = [int(re.search(r'\d+(?= degrees)', line).group()) for line in cpu_temp_lines if re.search(r'\d+(?= degrees)', line)]
        avg_cpu_temp = sum(cpu_temps) // len(cpu_temps)
        return avg_cpu_temp
    else:
        print("Failed to retrieve CPU temperature.")
        return None

# Set the fan speed
def set_fan_speed(speed):
    global current_fan_speed
    current_fan_speed = speed

    # Convert the speed percentage to a hex value
    hex_speed = format(speed * 255 // 100, "02x")

    syslog.syslog(syslog.LOG_INFO, f"Hex Speed: {hex_speed}")

    # Get Fan Zones Settings
    fan_zone_0 = CONFIG["ipmi"]["fan_zones"][0]["registers"]
    fan_zone_1 = CONFIG["ipmi"]["fan_zones"][1]["registers"]

    # Set the Fan Speed for Zone 0
    os.system(f"ipmitool raw {' '.join(fan_zone_0)} 0x{hex_speed}")
    time.sleep(2)

    # Set the Fan Speed for Zone 1
    os.system(f"ipmitool raw {' '.join(fan_zone_1)} 0x{hex_speed}")
    time.sleep(2)

    # Log the Fan Speed change to syslog
    syslog.syslog(syslog.LOG_INFO, f"Fan speed adjusted to {speed}%")

    # Print the Fan Speed change to console
    print(f"Fan speed adjusted to {speed}% - Hex: 0x{hex_speed}")


# Loop Method
# Infinite Loop
def loop():
    while True:
        # Get current CPU Temperatures
        cpu_temp = get_cpu_temperatures()

        # Print current CPU Temperature to Console
        print(f"Current CPU Temperature: {cpu_temp}°C")

        # Get current RAM Temperatures
        # ...

        # Get current Chipset Temperatures
        # ...

        # Get current HBA Temperatures
        # ...

        # Get current HDD / SSD / NVME Temperatures
        drives_temps_all = get_drives_temperatures()
        drives_temps_max = max(drives_temps_all)
        print(f"Maximum Drive Temperature: {drives_temps_max}°C")

        # Initialize new_fan_speed = current_fan_speed
        new_fan_speed_cpu = current_fan_speed
        new_fan_speed_drive = current_fan_speed


        # Regulate Fan Speed based on CPU Temperature
        if cpu_temp > CONFIG["cpu"]["max_temp"] and new_fan_speed_cpu < CONFIG["fan"]["max_speed"]:
            # Echo
            print(f"Increasing Fan Speed since CPU Temperature = {cpu_temp} is higher than the Maximum Setting = {CONFIG['cpu']['max_temp']}")

            # Increase the fan speed by CONFIG["fan"]["inc_speed_step"]% to cool down the CPU
            new_fan_speed_cpu = min(new_fan_speed_cpu + CONFIG["fan"]["inc_speed_step"], CONFIG["fan"]["max_speed"])
        elif cpu_temp < CONFIG["cpu"]["min_temp"] and new_fan_speed_cpu > CONFIG["fan"]["min_speed"]:
            # Echo
            print(f"Decreasing Fan Speed since CPU Temperature = {cpu_temp} is lower than the Minimum Setting = {CONFIG['cpu']['min_temp']}")

            # Decrease the fan speed by CONFIG["fan"]["dec_speed_step"]% if the temperature is below the minimum threshold
            new_fan_speed_cpu = max(new_fan_speed_cpu - CONFIG["fan"]["dec_speed_step"], CONFIG["fan"]["min_speed"])
            
        # Regulate Fan Speed based on Drives Temperature
        if drives_temps_max > CONFIG["drive"]["max_temp"] and new_fan_speed_drive < CONFIG["fan"]["max_speed"]:
            # Echo
            print(f"Increasing Fan Speed since Drive Temperature = {drives_temps_max} is higher than the Maximum Setting = {CONFIG['drive']['max_temp']}")

            # Increase the fan speed by CONFIG["fan"]["inc_speed_step"]% to cool down the Drives
            new_fan_speed_drive = min(new_fan_speed_drive + CONFIG["fan"]["inc_speed_step"], CONFIG["fan"]["max_speed"])
        elif drives_temps_max < CONFIG["drive"]["min_temp"] and new_fan_speed_drive > CONFIG["fan"]["min_speed"]:
            # Echo
            print(f"Decreasing Fan Speed since Drive Temperature = {drives_temps_max} is lower than the Minimum Setting = {CONFIG['drive']['min_temp']}")
            
            # Decrease the fan speed by CONFIG["fan"]["dec_speed_step"]% if the temperature is below the minimum threshold
            new_fan_speed_drive = max(new_fan_speed_drive - CONFIG["fan"]["dec_speed_step"], CONFIG["fan"]["min_speed"])

        # Get worst Case
        new_fan_speed = max([new_fan_speed_cpu , new_fan_speed_drive])

        # Set Fan Speed
        if new_fan_speed != current_fan_speed:
            set_fan_speed(new_fan_speed)

        # Wait UPDATE_INTERVAL seconds before checking the temperature again
        #pprint.pprint(CONFIG)
        time.sleep(CONFIG["general"]["update_interval"])



def configure():
    # Read General Configuration
    read_config(f"/etc/supermicro-fan-control/settings.yaml.default")
    read_config(f"/etc/supermicro-fan-control/settings.yaml")

    # Print Configuration
    #pprint.pprint(CONFIG)
    #print(json.dumps(CONFIG, indent=4, sort_keys=True))

    # Extract Configuration Variables
    general = CONFIG['general']
    motherboard = general['motherboard']

    # Read IPMI Configuration
    read_config(f"/etc/supermicro-fan-control/ipmi.d/default.yaml")
    read_config(f"/etc/supermicro-fan-control/ipmi.d/{motherboard}.yaml")

    # Print Configuration
    #pprint.pprint(CONFIG)
    #print(json.dumps(CONFIG, indent=4, sort_keys=True))

    # Echo
    print(f"Setting Fan Control Mode for Full (Manual)")

    # IPMI tool command to set the fan control mode to manual (Full)   
    fan_speed_full = CONFIG["ipmi"]["fan_modes"]["full"]["registers"]
    os.system(f"ipmitool raw {' '.join(fan_speed_full)}")
    time.sleep(2)

    # Stop here for now
    #sys.exit(0)

# Main Method
if __name__ == "__main__":
    # Initialize
    init()

    # Configure
    configure()

    # Set initial minimum fan speed
    print(f"Set Initial Fan Speed to {current_fan_speed}")
    set_fan_speed(current_fan_speed)

    # Run Control Loop
    loop()
