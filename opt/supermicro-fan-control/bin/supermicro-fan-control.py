#!/opt/supermicro-fan-control/venv/bin/python3

# Core Libraries
import os
import sys
import subprocess
import time
import syslog
import re
import math
import csv

# Python Modules to interact with YAML Files
import yaml
from yaml.loader import SafeLoader

# Python Pretty Print Module
import pprint

# Python json Module
import json

# Python datetime Module
from datetime import datetime

# Python DiskInfo Module
from diskinfo import Disk, DiskInfo, DiskType

# Import Custom Command Library
from modules.Command import Command

# Define Configuration Dictionary
CONFIG = dict()

# Initialize minimum Fan Speed to 50%
# Will be overridden by CONFIG["fan"]["min_speed"] in case that Value is Higher than this
current_fan_speed = 50               # [%] Current Fan Speed

# Log
def log(message , level="INFO" , indent=1):
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


# https://stackoverflow.com/questions/7204805/deep-merge-dictionaries-of-dictionaries-in-python
def deep_merge_lists(original, incoming):
    """
    Deep merge two lists. Modifies original.
    Recursively call deep merge on each correlated element of list. 
    If item type in both elements are
     a. dict: Call deep_merge_dicts on both values.
     b. list: Recursively call deep_merge_lists on both values.
     c. any other type: Value is overridden.
     d. conflicting types: Value is overridden.

    If length of incoming list is more that of original then extra values are appended.
    """
    common_length = min(len(original), len(incoming))
    for idx in range(common_length):
        if isinstance(original[idx], dict) and isinstance(incoming[idx], dict):
            deep_merge_dicts(original[idx], incoming[idx])

        elif isinstance(original[idx], list) and isinstance(incoming[idx], list):
            deep_merge_lists(original[idx], incoming[idx])

        else:
            original[idx] = incoming[idx]

    for idx in range(common_length, len(incoming)):
        original.append(incoming[idx])

# https://stackoverflow.com/questions/7204805/deep-merge-dictionaries-of-dictionaries-in-python
def deep_merge_dicts(original, incoming):
    """
    Deep merge two dictionaries. Modifies original.
    For key conflicts if both values are:
     a. dict: Recursively call deep_merge_dicts on both values.
     b. list: Call deep_merge_lists on both values.
     c. any other type: Value is overridden.
     d. conflicting types: Value is overridden.

    """
    for key in incoming:
        if key in original:
            if isinstance(original[key], dict) and isinstance(incoming[key], dict):
                deep_merge_dicts(original[key], incoming[key])

            elif isinstance(original[key], list) and isinstance(incoming[key], list):
                deep_merge_lists(original[key], incoming[key])

            else:
                original[key] = incoming[key]
        else:
            original[key] = incoming[key]


# Merge Configuration
# If a Key is defined in both config_a and config_b, the Value of config_b will override the Value of config_a
def merge_config(config_a , config_b):

    # Initialize config as config_a
    config = config_a.copy()

    # Echo
    log(f"Merging Configuration" , level="DEBUG")
    log(f"Previous Configuration:" , level="DEBUG")

    # Display Current Configuration
    print(config)

    # Echo
    log(f"Updated Configuration:" , level="DEBUG")

    # Deep Merge Configuration
    deep_merge_dicts(config , config_b)

    # Display Updated Configuration
    print(config)

    # Return Result
    return config

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

# Check if string is float
def isfloat(text):
    try:
        float(text)
        return True
    except ValueError:
        return False

# Check if string is int
def isint(text):
    try:
        int(text)
        return True
    except ValueError:
        return False

# Get the System Event Log(s) filtered
def get_system_event_log_filtered(filter = ""):
    # Check if any Events occurred at all
    #has_events = subprocess.check_output(f"ipmitool -c sel | grep -i 'Entries' | sed -E 's|^Entries\\s*?:\\s*?([0-9]*)$|\\1|'" , shell=True).decode()
    #has_events = run_cmd(["ipmitool", "-c" , "sel" , "|" , "grep" , "-i" , "'Entries'" , "|" , "sed" , "-E" , "'s|^Entries\\s*?:\\s*?([0-9]*)$|\\1|'"] , check_return_code=False , return_result=True)
    has_events = run_cmd_pipes([["ipmitool" , "-c" , "sel"] , ["grep" , "-i" , "Entries"] , ["sed" , "-E" , "'s|^Entries\\s*?:\\s*?([0-9]*)$|\\1|'"]])
   
    # Initialize as None by Default
    system_event_log = None

    # Echo
    log(f"System Event Log: check if System had any Events Logged" , level="DEBUG")

    # Only get System Event Log if there are Events registered, otherwise we'll have Errors later
    if has_events is not None and len(has_events) > 0:
        # If a multi-line Output is returned, just grab the first Line
        has_events_split = has_events.split('\n')
        if isinstance(has_events_split , list):
            events = has_events_split[0]
        else:
            events = has_events_split

        # Echo
        log(f"System Event Log: {events} (RAW) Events have been Logged" , level="DEBUG")

        if isint(events):
            # Get Number of Event
            Nevents = int(events)

            if Nevents > 0:
                # Echo
                log(f"System Event Log: {Nevents} (Numeric) Events have been Logged" , level="DEBUG")

                # Get System Events according to Filter
                #system_event_log = subprocess.run(f"ipmitool -c sel elist | grep -Ei '{filter}'" , shell=True).decode()
                system_event_log = run_cmd(["ipmitool" , "-c" , "sel" , "elist" , "|" , "grep" , "-Ei" , "'{filter}'"] , check_return_code=False , return_result=True)
            else:
                # Echo
                log(f"System Event Log: Invalid Response Received (zero-Length) -> {events}" , level="DEBUG")
        else:
            # Echo
            log(f"System Event Log: Invalid Response Received (non-Integer) -> {events}" , level="DEBUG")

    else:
        # Echo
        log(f"System Event Log: Command returned None or Zero-Length" , level="DEBUG")

    # Return Output
    return system_event_log

# Get the System Event Log(s)
def get_system_event_log(log_all = True , log_fans = True , log_temperatures = True):
    # Declare Variables
    system_event_log = ""
    system_event_types = ""
    system_event_filter = ""

    if log_all:
        # Get All System Events

        # Define Type & Filter
        system_event_type = "ALL"
        system_event_filter = ""

    if log_fans:
        # Get Fan System Events

        # Define Type & Filter
        system_event_type = "FAN"
        system_event_filter = "FAN"

    if log_temperatures:
        # Get Temperature System Events

        # Define Type & Filter
        system_event_type = "TEMPERATURE"
        system_event_filter = "TEMP"

    # Get System Events
    system_event_log = get_system_event_log_filtered(filter = system_event_filter)

    # Process Results

    # If anything was returned
    if system_event_log:
        # Split Event Log by Line
        reader = csv.reader(system_event_log.split('\n'), delimiter=',' , quoting=csv.QUOTE_ALL)

        
        #reader = system_event_log.split('\n')

        # Process each Line Individually
        for row in reader:
            # If Array is NOT empty
            if row is not None and len(row) > 0:
                # Format: <id>,<date>,<time>,<component>,<threshold>,<action>,<message>
                # <time> obtained via `ipmitool` is already with the correct Time Zone. On the IPMI Web Interface, <time> **might** be UTC or a different Time Zone
                
                # Extract Values
                event_id = row[0]
                event_date_raw = row[1]
                event_time_raw = row[2]
                event_component = row[3]
                event_threshold = row[4]
                event_action = row[5]
                event_message = row[6]

                # Format Date
                #datetime.datetime.strptime("2013-1-25", '%Y-%m-%d').strftime('%m/%d/%y')
                event_date = event_date_raw
                event_time = event_time_raw

                # Log Event
                log(f"System Event Log: [{event_component}] Event ID {event_id} on {event_date} at {event_time}: {event_message} (Threshold: {event_threshold} , Action: {event_action})" , level="WARNING")
        
        # Remind User to clear System Event Log
        log(f"System Event Log: Please Fix the Problem then clear the System Event Log !" , level="INFO")

    # If no Entries exist in the System Event Log
    else:
        # Echo
        log(f"System Event Log: no Entries exist in the System Event Log." , level="DEBUG")

# Get the current Fan Speed(s)
def get_fan_speeds():
    fan_speed_lines = subprocess.check_output("ipmitool -c sensor | grep -Ei '^FAN|^MB-FAN|^BPN-FAN'" , shell=True).decode()
    
    if fan_speed_lines:
        #for fan_speed in fan_speed_lines:
        #    print(f"Fan Speed: {fan_speed}")
        reader = csv.reader(fan_speed_lines.split('\n'), delimiter=',')
        for row in reader:
            # If Array is NOT empty
            if row is not None and len(row) > 0:
                # Get Label
                label = row[0]

                # Get Value
                value = row[1]

                # If Speed is a valid Number
                if isfloat(value) is True:
                    number = float(value)
                    #if not math.isnan(number) and not math.isinf(number):
                    log(f"Current {label} Fan Speed: {number} rpm" , level="DEBUG")

# Set the fan speed
def set_fan_speed(speed):
    # speed: integer between 0 and 100 (possibly further limited to CONFIG["fan"]["min_speed"] and CONFIG["fan"]["max_speed"])
    
    # Allow to update Global Variables
    global current_fan_speed

    # Set the Current Fan Speed (Reference) to the speed Input we receive
    current_fan_speed = speed

    # Convert the speed percentage to a hex value
    # !! The 255/100 does NOT seem to be correct, at least on some Motherboards !!
    # hex_speed = format(speed * 255 // 100, "02x")

    # Convert the speed percentage to a hex value
    # Use max_speed_hex and min_speed_hex from CONFIG

    # For each Fan Zones Settings
    for fan_zone in CONFIG["ipmi"]["fan_zones"]:
        # Extract Parameters
        fan_zone_id = fan_zone["id"]
        fan_zone_name = fan_zone["name"]
        fan_zone_description = fan_zone["description"]
        fan_zone_registers = fan_zone["registers"]
        fan_zone_max_speed_hex = fan_zone["max_speed_hex"]
        fan_zone_min_speed_hex = fan_zone["min_speed_hex"]
        
        # Convert Hexadecimal Max / Min Zone Fan Speed to Decimal
        fan_zone_max_speed_dec = int(fan_zone_max_speed_hex , 16)
        fan_zone_min_speed_dec = int(fan_zone_min_speed_hex , 16)

        # Scale according to 0% - 100%
        fan_zone_speed_dec = fan_zone_min_speed_dec + (fan_zone_max_speed_dec - fan_zone_min_speed_dec) / (100-0) * (speed - fan_zone_min_speed_dec)

        # Convert to Integer
        fan_zone_speed_dec = int(fan_zone_speed_dec)

        # Calculate HEX Speed
        fan_zone_speed_hex = format(fan_zone_speed_dec , "02x")

        # Echo
        log(f"Fan Controller: Setting Fan Zone {fan_zone_id} ({fan_zone_description}) to {fan_zone_speed_dec}% (Hex Speed Value to 0x{fan_zone_speed_hex})" , "INFO")

        # Set the Fan Speed for Zone
        run_cmd(["ipmitool" , "raw"] + fan_zone_registers + [f"0x{fan_zone_speed_hex}"])
        time.sleep(2)

        # Log the Fan Speed change to syslog
        log(f"Fan Controller: Fan Zone {fan_zone_id} ({fan_zone_description}) Speed has been adjusted to {fan_zone_speed_dec}% (Hex Value 0x{fan_zone_speed_hex})" , level="INFO")


# Run Temperature Controller
def run_temperature_controller(label , id , current_temp , current_fan_speed):
    if current_temp is not None:
        # Initialize Variable
        new_fan_speed = current_fan_speed

        if current_temp > CONFIG[id]["max_temp"] and new_fan_speed < CONFIG["fan"]["max_speed"]:
            # Echo
            log(f"{label} Temperature Controller: Increasing Fan Speed Reference since {label} Controller Temperature = {current_temp}°C is higher than the Maximum Setting = {CONFIG[id]['max_temp']}°C" , level="DEBUG")

            # Increase the fan speed by CONFIG["fan"]["inc_speed_step"]% to cool down the <id>
            new_fan_speed = min(new_fan_speed + CONFIG["fan"]["inc_speed_step"], CONFIG["fan"]["max_speed"])

            # Echo
            log(f"{label} Temperature Controller: New Fan Speed Reference based on {label} Controller Temperature: {new_fan_speed}%" , level="DEBUG")

        elif current_temp < CONFIG[id]["min_temp"] and new_fan_speed > CONFIG["fan"]["min_speed"]:
            # Echo
            log(f"{label} Temperature Controller: Decreasing Fan Speed Reference since {label} Temperature = {current_temp}°C is lower than the Minimum Setting = {CONFIG[id]['min_temp']}°C" , level="DEBUG")

            # Decrease the fan speed by CONFIG["fan"]["dec_speed_step"]% if the temperature is below the minimum threshold
            new_fan_speed = max(new_fan_speed - CONFIG["fan"]["dec_speed_step"], CONFIG["fan"]["min_speed"])

            # Echo
            log(f"{label} Temperature Controller: New Fan Speed Reference based on {label} Controller Temperature: {new_fan_speed}%" , level="DEBUG")
        else:
            if new_fan_speed >= CONFIG["fan"]["max_speed"]:
                # Echo
                log(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since Current Fan Speed {current_fan_speed} is already >= {CONFIG['fan']['max_speed']}°C" , level="DEBUG")

            elif new_fan_speed <= CONFIG["fan"]["min_speed"]:
                # Echo
                log(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since Current Fan Speed {current_fan_speed} is already <= {CONFIG['fan']['min_speed']}°C" , level="DEBUG")

            elif current_temp >= CONFIG[id]['min_temp'] and current_temp <= CONFIG[id]['max_temp']:
                # Echo
                log(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since {label} Temperature = {current_temp}°C is within Histeresis Range = [{CONFIG[id]['min_temp']}°C ... {CONFIG[id]['max_temp']}°C]" , level="DEBUG")

        # Return Result
        return new_fan_speed
    else:
        # Echo
        log(f"{label} Temperature Controller: No Devices of Type {label} are installed. No Action will be performed for {label} Temperature Regulation.")

        # Return Zero
        return 0

# Run Drives (HDD/SSD/NVME) Temperature Protection
def run_temperature_protection(label , id , current_temp):
    if current_temp is not None:
        if current_temp >= CONFIG[id]["shutdown_temp"]:
            # Echo
            log(f"{label} OverTemperature Protection: Temperature = {current_temp}°C is higher than the Shutdown Setting = {CONFIG[id]['shutdown_temp']}°C" , level="CRITICAL")
            log(f"{label} OverTemperature Protection: Shutting Down System Now" , level="CRITICAL")

            # Wait a bit to make sure we logged everything
            time.sleep(2)

            # SHUTDOWN to prevent Damage
            os.system(f"shutdown -h now")
        if current_temp >= CONFIG[id]["warning_temp"] and current_temp < CONFIG[id]["shutdown_temp"]:
            # Echo
            log(f"{label} OverTemperature Protection: Temperature = {current_temp}°C is higher than the Warning Setting = {CONFIG[id]['warning_temp']}°C" , level="WARNING")
            log(f"{label} OverTemperature Protection: Sounding BEEP on the Speaker" , level="WARNING")

            # BEEP Warning

            # Harcoded Values
            #os.system(f"beep -f 2500 -l 2000 -r 5 -D 1000")

            # Configurable Values
            os.system(f"beep -f {CONFIG['beep']['frequency']} -l {CONFIG['beep']['duration']} -r {CONFIG['beep']['repetitions']} -D {CONFIG['beep']['delay']}")
        elif current_temp < CONFIG[id]["warning_temp"]:
            # Echo
            log(f"{label} OverTemperature Protection: {label} Temperature = {current_temp}°C is lower than the {label} OverTemperature Warning Setting = {CONFIG[id]['warning_temp']}°C. No Action required." , level="DEBUG")
        else:
            # Echo
            log(f"{label} OverTemperature Protection: Did NOT match any IF Condition. Temperature = {current_temp}°C. {label} OverTemperature Warning Setting = {CONFIG[id]['warning_temp']}°C. {label} OverTemperature Shutdown Setting = {CONFIG[id]['shutdown_temp']}°C. Investigation required.." , level="WARNING")
    else:
        # Echo
        log(f"{label} OverTemperature Protection: No Devices of Type {label} are installed. No Action will be performed for {label} OverTemperature Protection.")

# Run Command (simple, without Pipes)
# To be implemented in the future in Order to Detect Errors returned by e.g. ipmitool
def run_cmd(command , return_result = False , check_return_code = True):
    # Echo Command
    log(f"Running Command: {' '.join([str(item) for item in command])}" , level="DEBUG")
    log(f"Command Array: {command}" , level="DEBUG")

    # Run Command
    result_cmd = subprocess.run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True , text=True)

    if result_cmd.returncode != 0:
        text_cmd = result_cmd.stderr.rsplit("\n")
        log(f"Command exited with a non-Zero Error Code" , level="ERROR")
        log(f"{result_cmd.stderr}" , level="ERROR")
    else:
        text_cmd = result_cmd.stdout.rsplit("\n")

    # Return result
    if return_result:
        return text_cmd

# Run Command (complex, with Pipes)
# To be implemented in the future in Order to Detect Errors returned by e.g. ipmitool
def run_cmd_pipes(command , return_result = False , check_return_code = True , debug_output = False):
    # Encapsulate everything in an external List if it's not already the Case
    if not isinstance(command[0] , list):
        new_command = [command]
    else:
        new_command = command

    rows = len(new_command)
    cols = len(new_command[0])

    trows = type(new_command)
    tcols = type(new_command[0])
    Npipes = len(new_command)

    #print(f"Array Dimension: {rows} Rows x {cols} Columns")
    #print(f"Types: {trows} (Rows) - {tcols} (Cols)")

    # Build Command String
    running_cmd_text = ""
    for p in range(Npipes):
        # String of each Pipe Command
        pipe_cmd_text = ' '.join([str(item) for item in new_command[p]])

        # Join into a single String Command
        if running_cmd_text == "":
            running_cmd_text = pipe_cmd_text
        else:
            running_cmd_text = " | ".join([running_cmd_text , pipe_cmd_text])

    # Echo Overall Command
    log(f"Running Command (Complete String): {running_cmd_text}" , level="DEBUG")
    log(f"Running Command (Complete Array): {new_command}" , level="DEBUG")

    # Initialize the Proc Lists
    pobject = [None] * Npipes
    pstdout = [None] * Npipes
    pstderr = [None] * Npipes
    preturncode = [None] * Npipes

    # Echo
    log(f"Processing Command Pipe: {new_command[0]}" , level="DEBUG" , indent=1)

    # Execute the first Command
    pobject[0] = subprocess.Popen(' '.join(new_command[0]) , shell=True , stdin=subprocess.PIPE , stdout=subprocess.PIPE , stderr=subprocess.PIPE)
    #proc[0] = subprocess.run(new_command[0] , stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True , text=True)

    # Store results
    pstdout[0] , pstderr[0] = pobject[0].communicate()

    # Save Return Code
    preturncode[0] = pobject[0].wait()

    # Echo
    print(pstdout[0].decode())
    print(pstderr[0].decode())
    

    # Execute all Subsequent Pipes
    if Npipes > 1:
        for p in range(1 , Npipes , 1):
            # Echo
            log(f"Processing Command Pipe: {new_command[p]}" , level="DEBUG" , indent=1)

            # Get Result for the Current Pipe
            #proc[p] = subprocess.Popen(new_command[p], stdin=proc[p-1].stdout,
            #                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Allow proc[p-1] to receive a SIGPIPE if proc[p] exits.
            #proc[p-1].stdout.close()
            #out, err = proc[p].communicate()

            # Just use Run
            #proc[p] = subprocess.run(new_command[p] , input=proc[p-1].stdout , stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True , text=True)

            # Use Pipe
            pobject[p] = subprocess.Popen(' '.join(new_command[p]) , shell=True , stdin=subprocess.PIPE , stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Provide Input Data

            # Fetch Result
            pstdout[p] , pstderr[p] = pobject[p].communicate(input=pstdout[p-1])

            # Save Return Code
            preturncode[p] = pobject[p].wait()

            print(pstdout[p].decode())
            print(pstderr[p].decode())

    # Get Final Result
    #result_cmd = pstdout[-1]

    # Check if any Return Code is non-Zero
    #if any(preturncode):
    #    text_cmd = pstdout[-1].rsplit("\n")
    #    log(f"Command exited with a non-Zero Error Code" , level="ERROR")
    #    log(f"{pstderr[-1]}" , level="ERROR")
    #else:
    #    text_cmd = pstdout[-1].rsplit("\n")

    # Return result
    if return_result:
        return text_cmd

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
        hdd_count = len(hdd_temps_all)
        if hdd_temps_all is not None and hdd_count > 0:
            hdd_temps_max = max(hdd_temps_all)
            log(f"Maximum HDD Temperature: {hdd_temps_max}°C" , level="INFO")
        else:
            hdd_temps_max = None
            log(f"No HDD Detected" , level="INFO")

        # Get current SSD Temperatures
        ssd_temps_all = get_drives_temperatures(filterType = DiskType.SSD)
        ssd_count = len(ssd_temps_all)
        if ssd_temps_all is not None and ssd_count > 0:
            ssd_temps_max = max(ssd_temps_all)
            log(f"Maximum SSD Temperature: {ssd_temps_max}°C" , level="INFO")
        else:
            ssd_temps_max = None
            log(f"No SSD Detected" , level="INFO")

        # Get current NVME Temperatures
        nvme_temps_all = get_drives_temperatures(filterType = DiskType.NVME)
        nvme_count = len(nvme_temps_all)
        if nvme_temps_all is not None and nvme_count > 0:
            nvme_temps_max = max(nvme_temps_all)
            log(f"Maximum NVME Temperature: {nvme_temps_max}°C" , level="INFO")
        else:
            nvme_temps_max = None
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
            log(f"Fan Controller: Updating Fan Speed from {current_fan_speed}% to {new_fan_speed}%." , level="INFO")

            # Update
            set_fan_speed(new_fan_speed)
        else:
            # Echo
            log(f"Fan Controller: No Fan Speed Update required. Keeping Fan Speed to {current_fan_speed}% but sending Reference Again." , level="DEBUG")

            # Prevent e.g. (external) manual testing from "blocking" the Fan Speed to a Low Value in case Fan Speed is already at 100%
            set_fan_speed(new_fan_speed)

        # Get and Log Current Fan Speed
        get_fan_speeds()

        # Get and Log IPMI System Event Log
        get_system_event_log()

        # Wait UPDATE_INTERVAL seconds before checking the temperature again
        #pprint.pprint(CONFIG)
        time.sleep(CONFIG["general"]["update_interval"])



def configure():
    # Get Configuration Folder
    SUPERMICRO_FAN_CONTROL_CONFIG_PATH = os.getenv("SUPERMICRO_FAN_CONTROL_CONFIG_PATH") 

    if SUPERMICRO_FAN_CONTROL_CONFIG_PATH is None:
        SUPERMICRO_FAN_CONTROL_CONFIG_PATH = "/etc/supermicro-fan-control/"

    # Echo
    log(f"Using Configuration Folder {SUPERMICRO_FAN_CONTROL_CONFIG_PATH}" , level="INFO")

    # Read General Configuration
    read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/settings.yml.default")
    read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/settings.yml")

    # Print Configuration
    #pprint.pprint(CONFIG)
    #print(json.dumps(CONFIG, indent=4, sort_keys=True))

    # Extract Configuration Variables
    general = CONFIG['general']
    motherboard = general['motherboard']

    # Read IPMI Configuration
    read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/ipmi.d/default.yml")
    read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/ipmi.d/{motherboard}.yml")

    # Print Configuration
    #pprint.pprint(CONFIG)
    #print(json.dumps(CONFIG, indent=4, sort_keys=True))

    # Echo
    log(f"Setting Fan Control Mode to Optimal" , level="INFO")
    log(f"This is needed because in some cases the Fan Speed is stuck, if already starting in Full Mode" , level="INFO")

    # IPMI tool command to set the fan control mode to Optimal
    fan_speed_optimal = CONFIG["ipmi"]["fan_modes"]["optimal"]["registers"]
    run_cmd(["ipmitool" , "raw"] + fan_speed_optimal)
    time.sleep(2)

    # Echo
    log(f"Setting Fan Control Mode to Full (Manual)" , level="INFO")

    # IPMI tool command to set the fan control mode to manual (Full)
    fan_speed_full = CONFIG["ipmi"]["fan_modes"]["full"]["registers"]
    run_cmd(["ipmitool" , "raw"] + fan_speed_full)
    time.sleep(2)

    # Set the Correct Environment Variables
    for name in CONFIG["general"]["environment"]:
        # Get Value
        value = str(CONFIG["general"]["environment"][name])

        # Echo
        log(f"Environment: Set Environment Parameter {name} to {value}" , level="INFO")

        # Set the Variable
        os.environ[name] = value


# Main Method
if __name__ == "__main__":
    # Initialize
    init()

    # Configure
    configure()

    # Override the initial Setting for current_fan_speed in case CONFIG["fan"]["min_speed"] is higher
    current_fan_speed = max(current_fan_speed , CONFIG["fan"]["min_speed"])

    # Set initial minimum fan speed
    log(f"Set Initial Fan Speed to {current_fan_speed}%" , "INFO")
    set_fan_speed(current_fan_speed)

    # Testing
    get_system_event_log()

    # Run Control Loop
    #loop()
