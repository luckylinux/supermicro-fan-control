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
from diskinfo import Disk, DiskInfo, DiskType

# Subprocess Python Module
from subprocess import Popen , PIPE, run

# Define Configuration Dictionary
CONFIG = dict()

# Initialize minimum Fan Speed to 50%
current_fan_speed = 50               # [%] Current Fan Speed

# Log
def log(message , level="INFO"):
    # Echo
    print(f"[{level}] {message}")

    # syslog.syslog(syslog.LOG_INFO, f"Hex Speed: {hex_speed}")

    # Flush in order for Journalctl to show the newly added Lines
    sys.stdout.flush()

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
        log(f"Merging Configuration" , level="DEBUG")

        # Iterate over Existing Config
        for key, value in config.items():
            # Print Key
            #print(key)

            # If the key also exists in config_b, then replace value
            if key in config_b:
                # Echo
                log(f"Override Key {key} in config ({value} -> {config_b[key]})" , level="DEBUG")

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
            log(f"Add non-existing Key {key} in config ({config_b[key]})" , level="DEBUG")

            # Set Key
            config[key] = value

    else:
        # Simply use config_b
        log(f"config_a was empty/none: config_b will override everything" , level="WARNING")
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
        log(f"Loading File {filepath}", level="INFO")

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
                log(f"File {filepath} is empty" , level="WARNING")
    else:
        # Echo
        log(f"File {filepath} does NOT exist" , level="WARNING")

# Get the current HDD/SSD/NVME Temperature(s)
def get_drives_temperatures(filterType = None):
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
        driveType = d.get_type()
        driveTypeStr = d.get_type_str()

        # If it's a Physical Disk (i.e. it has a Valid Temperature)
        if temp is not None:
            if driveType == filterType or filterType is None:
                # Echo
                log(f"{driveTypeStr} Drive {filteredid} has Temperature = {temp}°C" , level="INFO")

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
        log("Failed to retrieve CPU temperature." , level="ERROR")
        return None

# Set the fan speed
def set_fan_speed(speed):
    global current_fan_speed
    current_fan_speed = speed

    # Convert the speed percentage to a hex value
    hex_speed = format(speed * 255 // 100, "02x")

    log(f"Hex Speed: 0x{hex_speed}%" , "INFO")

    # Get Fan Zones Settings
    fan_zone_0 = CONFIG["ipmi"]["fan_zones"][0]["registers"]
    fan_zone_1 = CONFIG["ipmi"]["fan_zones"][1]["registers"]

    # Set the Fan Speed for Zone 0
    #os.system(f"ipmitool raw {' '.join(fan_zone_0)} 0x{hex_speed}")
    run_cmd(["ipmitool" , "raw"] + fan_zone_0 + [f"0x{hex_speed}"])
    time.sleep(2)

    # Set the Fan Speed for Zone 1
    #os.system(f"ipmitool raw {' '.join(fan_zone_1)} 0x{hex_speed}")
    run_cmd(["ipmitool" , "raw"] + fan_zone_1 + [f"0x{hex_speed}"])
    time.sleep(2)

    # Log the Fan Speed change to syslog
    log(f"Fan speed adjusted to {speed}%" , level="INFO")

    # Print the Fan Speed change to console
    log(f"Fan speed adjusted to {speed}% - Hex: 0x{hex_speed}" , level="INFO")


# Run Temperature Controller
def run_temperature_controller(label , id , current_temp , current_fan_speed):
    # Initialize Variable
    new_fan_speed = current_fan_speed

    if current_temp > CONFIG[id]["max_temp"] and new_fan_speed < CONFIG["fan"]["max_speed"]:
        # Echo
        log(f"Increasing Fan Speed since {label} Controller Temperature = {current_temp}°C is higher than the Maximum Setting = {CONFIG[id]['max_temp']}°C" , level="DEBUG")

        # Increase the fan speed by CONFIG["fan"]["inc_speed_step"]% to cool down the <id>
        new_fan_speed = min(new_fan_speed + CONFIG["fan"]["inc_speed_step"], CONFIG["fan"]["max_speed"])

        # Echo
        log(f"New Fan Speed based on {label} Controller Temperature = {new_fan_speed}%" , level="DEBUG")

    elif current_temp < CONFIG[id]["min_temp"] and new_fan_speed > CONFIG["fan"]["min_speed"]:
        # Echo
        log(f"Decreasing Fan Speed since {label} Temperature = {current_temp}°C is lower than the Minimum Setting = {CONFIG[id]['min_temp']}°C" , level="DEBUG")

        # Decrease the fan speed by CONFIG["fan"]["dec_speed_step"]% if the temperature is below the minimum threshold
        new_fan_speed = max(new_fan_speed - CONFIG["fan"]["dec_speed_step"], CONFIG["fan"]["min_speed"])

        # Echo
        log(f"New Fan Speed based on {label} Controller Temperature = {new_fan_speed}%" , level="DEBUG")
    else:
        if new_fan_speed >= CONFIG["fan"]["max_speed"]:
            # Echo
            log(f"Skipping Fan Speed Update for {label} Controller since Current Fan Speed {current_fan_speed} is already >= {CONFIG['fan']['max_speed']}°C" , level="DEBUG")

        elif new_fan_speed <= CONFIG["fan"]["min_speed"]:
            # Echo
            log(f"Skipping Fan Speed Update for {label} Controller since Current Fan Speed {current_fan_speed} is already <= {CONFIG['fan']['min_speed']}°C" , level="DEBUG")

        elif current_temp >= CONFIG[id]['min_temp'] and current_temp <= CONFIG[id]['max_temp']:
            # Echo
            log(f"Skipping Fan Speed Update for {label} Controller since {label} Temperature = {current_temp}°C is within Histeresis Range = [{CONFIG[id]['min_temp']}°C ... {CONFIG[id]['max_temp']}°C]" , level="DEBUG")

    # Return Result
    return new_fan_speed

# Run Drives (HDD/SSD/NVME) Temperature Protection
def run_temperature_protection(label , id , current_temp):
    if current_temp >= CONFIG[id]["shutdown_temp"]:
        # Echo
        log(f"{label} Temperature = {current_temp}°C is higher than the Shutdown Setting = {CONFIG[id]['shutdown_temp']}°C" , level="CRITICAL")
        log(f"Shutting Down System Now" , level="CRITICAL")

        # Wait a bit to make sure we logged everything
        time.sleep(2)

        # SHUTDOWN to prevent Damage
        os.system(f"shutdown -h now")
    if current_temp >= CONFIG[id]["warning_temp"] and current_temp < CONFIG[id]["shutdown_temp"]:
        # Echo
        log(f"{label} Temperature = {current_temp}°C is higher than the Warning Setting = {CONFIG[id]['warning_temp']}°C" , level="WARNING")
        log(f"Sounding BEEP on the Speaker" , level="WARNING")

        # BEEP Warning

        # Harcoded Values
        #os.system(f"beep -f 2500 -l 2000 -r 5 -D 1000")

        # Configurable Values
        os.system(f"beep -f {CONFIG['beep']['frequency']} -l {CONFIG['beep']['duration']} -r {CONFIG['beep']['repetitions']} -D {CONFIG['beep']['delay']}")
    elif current_temp < CONFIG[id]["warning_temp"]:
        # Echo
        log(f"{label} Temperature = {current_temp}°C is lower than the Warning Setting = {CONFIG[id]['warning_temp']}°C. No Action required." , level="DEBUG")
    else:
        # Echo
        log(f"{label} Did NOT match any IF Condition. Temperature = {current_temp}°C. Warning Setting = {CONFIG[id]['warning_temp']}°C. Shutdown Setting = {CONFIG[id]['shutdown_temp']}°C. Investigation required.." , level="WARNING")


# Run Command
# To be implemented in the future in Order to Detect Errors returned by e.g. ipmitool
def run_cmd(command):
    # Echo Command
    log(f"Running Command: {' '.join([str(item) for item in command])}" , level="DEBUG")
    log(f"Command Array: {command}" , level="DEBUG")

    # Run Command
    result_cmd = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True , text=True)

    if result_cmd.returncode != 0:
        text_cmd = result_cmd.stderr.rsplit("\n")
        log(f"Command exited with a non-Zero Error Code" , level="ERROR")
        log(f"{result_cmd.stderr}" , level="ERROR")
    else:
        text_cmd = result_cmd.stdout.rsplit("\n")


# Loop Method
# Infinite Loop
def loop():
    while True:
        # Get current CPU Temperatures
        cpu_temp = get_cpu_temperatures()

        # Print current CPU Temperature to Console
        log(f"Current CPU Temperature: {cpu_temp}°C" , level="INFO")

        # Get current RAM Temperatures
        # ...

        # Get current Chipset Temperatures
        # ...

        # Get current HBA Temperatures
        # ...

        # Get current ALL Drive Temperatures
        #drives_temps_all = get_drives_temperatures()
        #drives_temps_max = max(drives_temps_all)
        #log(f"Maximum Drive Temperature: {drives_temps_max}°C" , level="INFO")

        # Get current HDD Temperatures
        hdd_temps_all = get_drives_temperatures(filterType = DiskType.HDD)
        if hdd_temps_all is not None and len(hdd_temps_all) > 0:
            hdd_temps_max = max(hdd_temps_all)
            log(f"Maximum HDD Temperature: {hdd_temps_max}°C" , level="INFO")
        else:
            hdd_temps_max = 0
            log(f"No HDD Detected" , level="INFO")

        # Get current SSD Temperatures
        ssd_temps_all = get_drives_temperatures(filterType = DiskType.SSD)
        if ssd_temps_all is not None and len(ssd_temps_all) > 0:
            ssd_temps_max = max(ssd_temps_all)
            log(f"Maximum SSD Temperature: {ssd_temps_max}°C" , level="INFO")
        else:
            ssd_temps_max = 0
            log(f"No SSD Detected" , level="INFO")

        # Get current NVME Temperatures
        nvme_temps_all = get_drives_temperatures(filterType = DiskType.NVME)
        if nvme_temps_all is not None and len(nvme_temps_all) > 0:
            nvme_temps_max = max(nvme_temps_all)
            log(f"Maximum NVME Temperature: {nvme_temps_max}°C" , level="INFO")
        else:
            nvme_temps_max = 0
            log(f"No NVME Detected" , level="INFO")

        # Initialize new_fan_speed = current_fan_speed
        new_fan_speed_cpu = current_fan_speed
        #new_fan_speed_drive = current_fan_speed
        new_fan_speed_hdd = current_fan_speed
        new_fan_speed_ssd = current_fan_speed
        new_fan_speed_nvme = current_fan_speed

        # Protect CPU Temperature
        # TO_BE_IMPLEMENTED

        # Regulate Fan Speed based on CPU Temperature
        new_fan_speed_cpu = run_temperature_controller(label = "CPU" , id = "cpu" , current_temp = cpu_temp , current_fan_speed = new_fan_speed_cpu)

        # Regulate Fan Speed based on Drives Temperature
        #new_fan_speed_drive = run_temperature_controller(label = "Drive" , id = "drive" , current_temp = drives_temps_max , current_fan_speed = new_fan_speed_drive)

        # Protect HDD Temperature
        run_temperature_protection(label = "HDD" , id = "hdd" , current_temp = hdd_temps_max)

        # Regulate Fan Speed based on HDD Temperature
        new_fan_speed_hdd = run_temperature_controller(label = "HDD" , id = "hdd" , current_temp = hdd_temps_max , current_fan_speed = new_fan_speed_hdd)

        # Protect SSD Temperature
        run_temperature_protection(label = "SSD" , id = "ssd" , current_temp = ssd_temps_max)

        # Regulate Fan Speed based on SSD Temperature
        new_fan_speed_ssd = run_temperature_controller(label = "SSD" , id = "ssd" , current_temp = ssd_temps_max , current_fan_speed = new_fan_speed_ssd)

        # Protect NVME Temperature
        run_temperature_protection(label = "NVME" , id = "nvme" , current_temp = nvme_temps_max)

        # Regulate Fan Speed based on NVME Temperature
        new_fan_speed_nvme = run_temperature_controller(label = "NVME" , id = "nvme" , current_temp = nvme_temps_max , current_fan_speed = new_fan_speed_nvme)


        # Get worst Case
        #new_fan_speed = max([new_fan_speed_cpu , new_fan_speed_drive])
        new_fan_speed = max([new_fan_speed_cpu , new_fan_speed_hdd , new_fan_speed_ssd , new_fan_speed_nvme])

        # Set Fan Speed
        if new_fan_speed != current_fan_speed:
            # Echo
            log(f"Updating Fan Speed from {current_fan_speed}% to {new_fan_speed}%" , level="INFO")

            # Update
            set_fan_speed(new_fan_speed)
        else:
            # Echo
            log(f"No Fan Speed Update required. Keeping Fan Speed to {current_fan_speed}%" , level="DEBUG")

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
    log(f"Setting Fan Control Mode to Optimal" , level="INFO")
    log(f"This is needed because in some cases the Fan Speed is stuck, if already starting in Full Mode" , level="INFO")

    # IPMI tool command to set the fan control mode to Optimal
    fan_speed_heavy_io = CONFIG["ipmi"]["fan_modes"]["optimal"]["registers"]
    run_cmd(["ipmitool" , "raw"] + fan_speed_heavy_io)
    time.sleep(2)

    # Echo
    log(f"Setting Fan Control Mode to Full (Manual)" , level="INFO")

    # IPMI tool command to set the fan control mode to manual (Full)
    fan_speed_full = CONFIG["ipmi"]["fan_modes"]["full"]["registers"]
    #os.system(f"ipmitool raw {' '.join(fan_speed_full)}")
    run_cmd(["ipmitool" , "raw"] + fan_speed_full)
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
    log(f"Set Initial Fan Speed to {current_fan_speed}%" , "INFO")
    set_fan_speed(current_fan_speed)

    # Run Control Loop
    loop()
