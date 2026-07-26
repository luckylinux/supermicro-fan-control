#!/usr/bin/env python3

# Core Libraries
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Path, status
from fastapi.security import OpenIdConnect
from pydantic import BaseModel, Field

import datetime

import uvicorn
import threading

import os
# import sys
# import subprocess
import time
# import syslog
import re
# import math
import csv
import argparse

# Python Modules to interact with YAML Files
import yaml
from yaml.loader import SafeLoader

# Python Pretty Print Module
# import pprint

# Python json Module
import json

# Python datetime Module
# from datetime import datetime

# Python DiskInfo Module
from diskinfo import DiskInfo, DiskType

# Import psutil Python Module
import psutil

# Subprocess Python Module
from subprocess import Popen , PIPE, run

# Import Global Variables List
import globals

# from globals import *
# import misc.Globals

# import globals.CONFIG as CONFIG
# import globals.LOG_LEVEL as LOG_LEVEL

# from globals.CONFIG import CONFIG
# from globals.LOG_LEVEL import LOG_LEVEL

# import misc.Globals as Globals
# misc.Globals.init()

# Import Custom Libraries
from misc.command import Command
from misc.logging import log
from misc.deep_merge import deep_merge_dicts, deep_merge_lists
from misc.datatypes import isint, isfloat



# Define LOG_LEVEL
# LOG_LEVEL = LogLevel.DEBUG

# Initialize minimum Fan Speed to 50%
# Will be overridden by global_data.config["fan"]["initial_speed"] in case that Value is Higher than this
default_initial_fan_speed = 50 # [%] Current Fan Speed

class Data:
    # Declare Attributes
    config: dict
    temperature_readings: dict
    fan_speed_readings: dict
    fan_speed_references: dict
    bmc_event_log: list

    # Class Constructor
    def __init__(self) -> None:
        # Initialize Configuration
        self.config = {}

        # Initialize Temperatures Reading
        self.temperature_readings = {}

        # Initialize Fan Speed Readings
        self.fan_speed_readings = {}

        # Initialize Fan Speed References
        self.fan_speed_references = {}

        # Initialize BMC Event Log
        self.bmc_event_log = []


# Pydantic Models (Data Documentation Layer)
# These declare exactly what structure your API outputs or inputs, providing Swagger with schema templates.
class MetricItem(BaseModel):
    name: str = Field(description="The unique system identifier for the hardware metric tracker.",
                      example="cpu_utilization"
                      )
    value: float = Field(description="The numerical measurement read during the most recent hardware cycle.",
                         example=42.8
                         )

class SystemStatusResponse(BaseModel):
    status: str = Field(description="The global runtime state indicator of the worker execution loop.",
                        example="healthy"
                        )
    timestamp: float = Field(description="The Unix epoch timestamp representing when this snapshot was requested.",
                             example=1719705600.0
                             )
    active_metrics: List[MetricItem] = Field(description="An array containing individual component readings captured by the system scanner.")


# Initialize Global State
global_data = Data()

# Initialize the OIDC Authentication Scheme
# FastAPI reads this to configure the interactive "Authorize" lock on Swagger UI.
# oidc_scheme = OpenIdConnect(openIdConnectUrl=OIDC_DISCOVERY_URL)

# Initialize API Application
api = FastAPI(title="Fan Controller API Endpoints",
              description="Fan Controller API Endpoints.",
              docs_url="/docs",
              redoc_url="/redoc",
              version="1.0.0",
              # swagger_ui_init_oauth={"clientId": "my-controller-client-id"}
              )

class GlobalController:
    # Class Constructor
    def __init__(self) -> None:
        # Init
        self.init()

    # Init
    def init(self):
        # Allow Function to modify CONFIG Global Variable
        # global CONFIG

        # Initialize CONFIG as a Dictionary
        # CONFIG = {}

        # Do nothing
        pass

    # Filter Drive
    def filter_drive(self,
                     path
                     ):
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
    def merge_config(self,
                     config_a: dict,
                     config_b: dict
                     ) -> dict:

        # Initialize config as config_a
        config = config_a.copy()

        # Display Current Configuration
        log("Previous Configuration:", level="DEBUG")
        print(json.dumps(global_data.config,
                        indent=4,
                        sort_keys=True
                        )
            )

        # Echo
        log("Merging Configuration:", level="DEBUG")

        # Deep Merge Configuration
        deep_merge_dicts(config, config_b)

        # Display Updated Configuration
        log("New Configuration:", level="DEBUG")
        print(json.dumps(global_data.config,
                        indent=4,
                        sort_keys=True
                        )
            )

        # Return Result
        return config

    # Read Configuration File
    def read_config(self,
                    filepath
                    ) -> None:
        # Allow Function to modify CONFIG Global Variable
        # global CONFIG

        # Debug
        # pprint.pprint(CONFIG)

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
                    global_data.config = self.merge_config(global_data.config , data)
                else:
                    # Echo
                    log(f"File {filepath} is empty" , level="WARNING")
        else:
            # Echo
            log(f"File {filepath} does NOT exist" , level="WARNING")

    # Get the current HDD/SSD/NVME Temperature(s)
    def get_drives_temperatures(self,
                                filterType = None
                                ) -> list | None:
        # Initialize Array
        temps = []
        drives = {}

        # Initialize Global Dictionary if needed
        if "drives" not in  global_data.temperature_readings:
            global_data.temperature_readings["drives"] = {}

        # Check all Disks
        di = DiskInfo()
        disks = di.get_disk_list(sorting=True)

        # Loop over Disks
        for d in disks:
            id = d.get_byid_path()
            filteredid = self.filter_drive(id)
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

                    # Add to Dictionary
                    drives.update({filteredid: temp})

        # global_data.temperature_readings["drives"]["average"] = avg_cpu_temp
        # global_data.temperature_readings["drives"]["minimum"] = max_cpu_temp
        # global_data.temperature_readings["drives"]["maximum"] = min_cpu_temp
        # global_data.temperature_readings["drives"]["details"] = temps

        match filterType:
            case DiskType.HDD:
                driveTypeStr = "hdd"
            case DiskType.SSD:
                driveTypeStr = "ssd"
            case DiskType.NVME:
                driveTypeStr = "nvme"
            case _:
                driveTypeStr = "unknown"

        if filterType is None:
            global_data.temperature_readings["drives"] = drives
        else:
            global_data.temperature_readings[driveTypeStr] = drives

        # Return Result
        return temps

    # Get the current CPU Temperature(s)
    def get_cpu_temperatures(self) -> float | int | None:

        # Initialize cpu_temps and core_temps to Empty Array
        cpu_temps = []
        core_temps = []

        # Check which Driver to Use
        if global_data.config["cpu"]["driver"] == "psutil":
            # Debug
            log(f"Extracting CPU Temperatures Data using psuitil Driver (cpu driver Setting in Configuration: {global_data.config['cpu']['driver']})" , level="DEBUG")

            # Use psutil Python Library to access Data Locally
            temperatures = psutil.sensors_temperatures()

            # Extract CPU Temperatures
            cpu_temperatures_all = temperatures['coretemp']

            if cpu_temperatures_all:
                # Extract CPUs and Cores Temperatures
                cpu_temps = [int(item.current) for item in cpu_temperatures_all if "Package id" in item.label]
                core_temps = [int(item.current) for item in cpu_temperatures_all if "Core" in item.label]
            else:
                log("Failed to retrieve CPU temperature using psutil.", level="ERROR")
                return None

        else:
            # Debug
            log(f"Extracting CPU Temperatures Data using ipmitool Driver (cpu driver Setting in Configuration: {global_data.config['cpu']['driver']})" , level="DEBUG")

            # Use Ipmitool to access Data
            cmd = ["ipmitool" , "sdr" , "type" , "temperature"]
            temp_output_obj = Command(command = cmd , return_result = True , check_return_code = True)
            time.sleep(2)
            temp_output = temp_output_obj.getOutput(decode=True)
            cpu_temp_lines = [line for line in temp_output.split("\n") if "CPU" in line and "degrees" in line]

            if cpu_temp_lines:
                # Extract CPUs Temperatures
                cpu_temps = [int(re.search(r'\d+(?= degrees)', line).group()) for line in cpu_temp_lines if re.search(r'\d+(?= degrees)', line)]
            else:
                log("Failed to retrieve CPU temperature using ipmitool.", level="ERROR")
                return None

        # Common Code
        # Data has already been extracted but can be processed in the same Way

        # Number of CPUs Detected on the System
        NCPUs = len(cpu_temps)

        # Log how many CPUs were Detected
        log(f"Number of CPUs Detected on this System: {NCPUs}" , level="DEBUG")

        # Print individual CPU Temperatures
        for cpu_index , cpu_temp in enumerate(cpu_temps): log(f"Current Temperatures of CPU {cpu_index}: {cpu_temp}" , level="DEBUG")

        # Print individual Core Temperatures (if available)
        if len(core_temps) > 0:
            for core_index , core_temp in enumerate(core_temps): log(f"Current Temperatures of Core {core_index}: {core_temp}" , level="DEBUG")

        # Calculate Average/Maximum Temperature between CPUs
        avg_cpu_temp = sum(cpu_temps) / len(cpu_temps)
        max_cpu_temp = max(cpu_temps) / 1.0
        min_cpu_temp = min(cpu_temps) / 1.0

        # Print Average / Maximum Value
        log(f"Average CPU temperature: {avg_cpu_temp}°C" , level="DEBUG")
        log(f"Maximum CPU temperature: {max_cpu_temp}°C" , level="DEBUG")

        # Create Structure to store Data
        # cpu_data = dict()

        # Store in Global Dictionary
        global_data.temperature_readings["cpu"] = {}
        global_data.temperature_readings["cpu"]["average"] = avg_cpu_temp
        global_data.temperature_readings["cpu"]["minimum"] = max_cpu_temp
        global_data.temperature_readings["cpu"]["maximum"] = min_cpu_temp
        global_data.temperature_readings["cpu"]["details"] = core_temps

        # Return one Value
        return avg_cpu_temp


    # Get the System Event Log(s) filtered
    def get_system_event_log_filtered(self,
                                      filter: str = "",
                                      label: str = ""
                                      ) -> None | Command:

        # Check if any Events occurred at all
        cmd = [["ipmitool" , "-c" , "sel"] , ["grep" , "-i" , "Entries"] , ["sed" , "-E" , "'s|^Entries\\s*?:\\s*?([0-9]*)$|\\1|'"]]
        events_obj = Command(command = cmd , return_result = True , check_return_code = True , debug = global_data.config["general"]["debug"])
        time.sleep(5)
        has_events = events_obj.getOutput(decode = True)

        # Initialize as None by Default
        system_event_log_obj = None

        # Echo
        log(f"System Event Log [{label}]: Checking if System had any Events Logged" , level="DEBUG")

        # Only get System Event Log if there are Events registered, otherwise we'll have Errors later
        if has_events is not None and len(has_events) > 0:
            # If a multi-line Output is returned, just grab the first Line
            has_events_split = has_events.split('\n')
            if isinstance(has_events_split , list):
                events = has_events_split[0]
            else:
                events = has_events_split

            # Echo
            log(f"System Event Log [{label}]: {events} (RAW) Events have been Logged" , level="DEBUG")

            if isint(events):
                # Get Number of Event
                Nevents = int(events)

                if Nevents > 0:
                    # Echo
                    log(f"System Event Log [{label}]: {Nevents} (Numeric) Events have been Logged" , level="DEBUG")

                    # Get System Events according to Filter
                    cmd = [["ipmitool" , "-c" , "sel" , "elist"] , ["grep" , "-Ei" , f"'{filter}'"]]
                    system_event_log_obj = Command(command = cmd , check_return_code = False , return_result = True , debug = global_data.config["general"]["debug"])
                    time.sleep(2)
                else:
                    # Echo
                    log(f"System Event Log [{label}]: System Log is Empty" , level="DEBUG")
            else:
                # Echo
                log(f"System Event Log [{label}]: Invalid Response Received (non-Integer Data) -> {events}" , level="DEBUG")

        else:
            # Echo
            log(f"System Event Log [{label}]: Command returned None or Zero-Length" , level="DEBUG")

        # Return Output
        return system_event_log_obj

    # Get the System Event Log(s)
    def get_system_event_log(self,
                             log_all: bool = True,
                             log_fans: bool = True,
                             log_temperatures: bool = True
                             ):
        # Declare Variables
        system_event_log = ""
        # system_event_types = ""
        system_event_filter = ""

        # Events
        events = []

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

        if log_all:
            # Get All System Events

            # Define Type & Filter
            system_event_type = "ALL"
            system_event_filter = ""

        # Get System Events
        system_event_log_obj = self.get_system_event_log_filtered(filter=system_event_filter,
                                                                  label=system_event_type
                                                                  )

        if system_event_log_obj:
            # System Log has some Entries
            system_event_log = system_event_log_obj.getOutput(decode = True)
        else:
            # System Log doesn't have any Entry
            system_event_log = None


        # Process Results

        # If anything was returned
        if system_event_log:
            # Split Event Log by Line
            reader = csv.reader(system_event_log.split('\n'),
                                delimiter=',',
                                quoting=csv.QUOTE_ALL
                                )


            #reader = system_event_log.split('\n')

            # Process each Line Individually
            for row in reader:
                #  Get Number of Elements
                Ncols = len(row)

                # If Array is NOT empty
                if row is not None and Ncols > 0:
                    # Format: <id>,<date>,<time>,<component>,<threshold>,<action>,<message>
                    # <time> obtained via `ipmitool` is already with the correct Time Zone. On the IPMI Web Interface, <time> **might** be UTC or a different Time Zone

                    # Extract Values
                    event_id = row[0]
                    event_date_raw = row[1]
                    event_time_raw = row[2]
                    event_component = row[3]
                    event_threshold = row[4]
                    event_action = row[5]

                    # Some IPMI Messages do NOT have all Columns
                    if Ncols >= 7:
                        event_message = row[6]
                    else:
                        event_message = ""

                    # Format Date
                    #datetime.datetime.strptime("2013-1-25", '%Y-%m-%d').strftime('%m/%d/%y')
                    event_date = event_date_raw
                    event_time = event_time_raw

                    # Log Event
                    log(f"System Event Log [{system_event_type}]: [{event_component}] Event ID {event_id} on {event_date} at {event_time}: {event_message} (Threshold: {event_threshold} , Action: {event_action})" , level="WARNING")

                    # Calculate UNIX Timestamp
                    # event_timestamp = ...
                    time_parts = event_time.split(" ")
                    clean_time = time_parts[0]  # This isolates "15:12:26"
                    tz_name = time_parts[1]     # This isolates "CET" (or "CEST")
                    # clean_time = event_time.replace(" CEST", "")

                    # 2. Combine and parse the numeric values
                    # %d/%m/%y handles Day/Month/Year (or %m/%d/%y for Month/Day/Year)
                    # dt_naive = datetime.datetime.strptime(f"{event_date} {clean_time}", "%d/%m/%y %H:%M:%S")
                    dt_naive = datetime.datetime.strptime(f"{event_date} {clean_time}", "%m/%d/%y %H:%M:%S")

                    if tz_name == "CEST":
                        offset_hours = 2  # Summer Time (UTC+2)
                    elif tz_name == "CET":
                        offset_hours = 1  # Standard Time (UTC+1)
                    else:
                        raise ValueError(f"Unknown timezone abbreviation: {tz_name}")

                    # 3. Explicitly attach the CEST timezone offset (UTC+2)
                    cest_tz = datetime.timezone(datetime.timedelta(hours=offset_hours))
                    dt_aware = dt_naive.replace(tzinfo=cest_tz)

                    # 4. Extract the Unix timestamp
                    event_timestamp = int(dt_aware.timestamp())

                    event = {}
                    event["id"] = event_id
                    event["type"] = system_event_type
                    event["date"] = event_date
                    event["time"] = event_time
                    event["timestamp"] = event_timestamp
                    event["component"] = event_component
                    event["threshold"] = event_threshold
                    event["action"] = event_action

                    events.append(event)

            # Remind User to clear System Event Log
            log(f"System Event Log [{system_event_type}]: Please Fix the Problem for Type {system_event_type} then clear the System Event Log !" , level="INFO")

        # If no Entries exist in the System Event Log
        else:
            # Echo
            log(f"System Event Log [{system_event_type}]: no Entries matching Type {system_event_type} exist in the System Event Log." , level="DEBUG")

        # Save in Global Data
        global_data.bmc_event_log = events

    # Get the current Fan Speed(s)
    def get_fan_speeds(self):
        cmd = [["ipmitool" , "-c" , "sensor"] , ["grep" , "-Ei" , "'^FAN|^MB-FAN|^BPN-FAN'"]]
        fan_speed_obj = Command(command = cmd , return_result = True , check_return_code = True)
        time.sleep(2)
        fan_speed_lines = fan_speed_obj.getOutput(decode=True)

        fan_speeds = {}

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
                        log(f"Current {label} Fan Speed: {number} rpm" , level="INFO")

                    # Add to Dictionary
                    fan_speeds.update({label: value})

            # Add to Global Data
            global_data.fan_speed_readings = fan_speeds

    # Set the fan speed
    def set_fan_speed(self,
                      speed
                      ) -> None:
        # speed: integer between 0 and 100 (possibly further limited to global_data.config["fan"]["min_speed"] and global_data.config["fan"]["max_speed"])

        # Allow to update Global Variables
        global current_fan_speed

        # Set the Current Fan Speed (Reference) to the speed Input we receive
        current_fan_speed = speed

        # Convert the speed percentage to a hex value
        # !! The 255/100 does NOT seem to be correct, at least on some Motherboards !!
        # hex_speed = format(speed * 255 // 100, "02x")

        # Convert the speed percentage to a hex value
        # Use max_speed_hex and min_speed_hex from global_data.config

        # For each Fan Zones Settings
        for fan_zone in global_data.config["ipmi"]["fan_zones"]:
            # Extract Parameters
            fan_zone_id = fan_zone["id"]
            # fan_zone_name = fan_zone["name"]
            fan_zone_description = fan_zone["description"]
            fan_zone_registers = fan_zone["registers"]
            fan_zone_max_speed_hex = fan_zone["max_speed_hex"]
            fan_zone_min_speed_hex = fan_zone["min_speed_hex"]

            # Convert Hexadecimal Max / Min Zone Fan Speed to Decimal
            fan_zone_max_speed_dec = int(fan_zone_max_speed_hex , 16)
            fan_zone_min_speed_dec = int(fan_zone_min_speed_hex , 16)

            # Scale according to (0% - 100%) and give Decimal Value (can be 0-100 or 0-255 Depending on Motherboards)
            fan_zone_speed_dec = fan_zone_min_speed_dec + (fan_zone_max_speed_dec - fan_zone_min_speed_dec) / (100-0) * (speed - fan_zone_min_speed_dec)

            # Convert to Integer
            fan_zone_speed_dec = int(fan_zone_speed_dec)

            # Convert to Percentage
            fan_zone_speed_percent = int((100 * fan_zone_speed_dec) / (fan_zone_max_speed_dec - fan_zone_min_speed_dec))

            # Calculate HEX Speed
            fan_zone_speed_hex = format(fan_zone_speed_dec , "02x")

            # Echo
            log(f"Fan Controller: Setting Fan Zone {fan_zone_id} ({fan_zone_description}) to {fan_zone_speed_percent}% (Decimal Speed Value {fan_zone_speed_dec}, Hex Speed Value 0x{fan_zone_speed_hex})" , "INFO")

            # Set the Fan Speed for Zone
            cmd = ["ipmitool" , "raw"] + fan_zone_registers + [f"0x{fan_zone_speed_hex}"]
            Command(command = cmd , return_result = False , check_return_code = True)
            time.sleep(2)

            # Log the Fan Speed change to syslog
            log(f"Fan Controller: Fan Zone {fan_zone_id} ({fan_zone_description}) Speed has been adjusted to {fan_zone_speed_percent}% (Decimal Speed Value {fan_zone_speed_dec}, Hex Value 0x{fan_zone_speed_hex})" , level="INFO")


    # Run Temperature Controller
    def run_temperature_controller(self,
                                   label,
                                   id,
                                   current_temp,
                                   current_fan_speed
                                   ) -> int:
        if current_temp is not None:
            # Initialize Variable
            new_fan_speed = current_fan_speed

            if current_temp > global_data.config[id]["max_temp"] and new_fan_speed < global_data.config["fan"]["max_speed"]:
                # Echo
                log(f"{label} Temperature Controller: Increasing Fan Speed Reference since {label} Controller Temperature = {current_temp}°C is higher than the Maximum Setting = {global_data.config[id]['max_temp']}°C" , level="DEBUG")

                # Increase the fan speed by global_data.config["fan"]["inc_speed_step"]% to cool down the <id>
                new_fan_speed = min(new_fan_speed + global_data.config["fan"]["inc_speed_step"], global_data.config["fan"]["max_speed"])

                # Echo
                log(f"{label} Temperature Controller: New Fan Speed Reference based on {label} Controller Temperature: {new_fan_speed}%" , level="DEBUG")

            elif current_temp < global_data.config[id]["min_temp"] and new_fan_speed > global_data.config["fan"]["min_speed"]:
                # Echo
                log(f"{label} Temperature Controller: Decreasing Fan Speed Reference since {label} Temperature = {current_temp}°C is lower than the Minimum Setting = {global_data.config[id]['min_temp']}°C" , level="DEBUG")

                # Decrease the fan speed by global_data.config["fan"]["dec_speed_step"]% if the temperature is below the minimum threshold
                new_fan_speed = max(new_fan_speed - global_data.config["fan"]["dec_speed_step"], global_data.config["fan"]["min_speed"])

                # Echo
                log(f"{label} Temperature Controller: New Fan Speed Reference based on {label} Controller Temperature: {new_fan_speed}%" , level="DEBUG")
            else:
                if new_fan_speed >= global_data.config["fan"]["max_speed"]:
                    # Echo
                    log(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since Current Fan Speed {current_fan_speed}% is already >= Fan Maximum Speed ({global_data.config['fan']['max_speed']}%)" , level="DEBUG")

                elif new_fan_speed <= global_data.config["fan"]["min_speed"]:
                    # Echo
                    log(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since Current Fan Speed {current_fan_speed}% is already <= Fan Minimum Speed ({global_data.config['fan']['min_speed']}%)" , level="DEBUG")

                if current_temp >= global_data.config[id]['min_temp'] and current_temp <= global_data.config[id]['max_temp']:
                    # Echo
                    log(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since {label} Temperature = {current_temp}°C is within Histeresis Range = [{global_data.config[id]['min_temp']}°C ... {global_data.config[id]['max_temp']}°C]" , level="DEBUG")

            # Return Result
            return new_fan_speed
        else:
            # Echo
            log(f"{label} Temperature Controller: No Devices of Type {label} are installed. No Action will be performed for {label} Temperature Regulation." , level="DEBUG")

            # Return Zero
            return 0

    # Run Drives (HDD/SSD/NVME) Temperature Protection
    def run_temperature_protection(self,
                                   label,
                                   id,
                                   current_temp
                                   ) -> None:

        if current_temp is not None:
            if current_temp >= global_data.config[id]["shutdown_temp"]:
                # Echo
                log(f"{label} OverTemperature Protection: Temperature = {current_temp}°C is higher than the Shutdown Setting = {global_data.config[id]['shutdown_temp']}°C" , level="CRITICAL")
                log(f"{label} OverTemperature Protection: Shutting Down System Now" , level="CRITICAL")

                # Wait a bit to make sure we logged everything
                time.sleep(2)

                # SHUTDOWN to prevent Damage
                os.system("shutdown -h now")
            if current_temp >= global_data.config[id]["warning_temp"] and current_temp < global_data.config[id]["shutdown_temp"]:
                # Echo
                log(f"{label} OverTemperature Protection: Temperature = {current_temp}°C is higher than the Warning Setting = {global_data.config[id]['warning_temp']}°C" , level="WARNING")
                log(f"{label} OverTemperature Protection: Sounding BEEP on the Speaker" , level="WARNING")

                # BEEP Warning

                # Harcoded Values
                #os.system(f"beep -f 2500 -l 2000 -r 5 -D 1000")

                # Configurable Values
                os.system(f"beep -f {global_data.config['beep']['frequency']} -l {global_data.config['beep']['duration']} -r {global_data.config['beep']['repetitions']} -D {global_data.config['beep']['delay']}")
            elif current_temp < global_data.config[id]["warning_temp"]:
                # Echo
                log(f"{label} OverTemperature Protection: {label} Temperature = {current_temp}°C is lower than the {label} OverTemperature Warning Setting = {global_data.config[id]['warning_temp']}°C. No Action required." , level="DEBUG")
            else:
                # Echo
                log(f"{label} OverTemperature Protection: Did NOT match any IF Condition. Temperature = {current_temp}°C. {label} OverTemperature Warning Setting = {global_data.config[id]['warning_temp']}°C. {label} OverTemperature Shutdown Setting = {global_data.config[id]['shutdown_temp']}°C. Investigation required.." , level="WARNING")
        else:
            # Echo
            log(f"{label} OverTemperature Protection: No Devices of Type {label} are installed. No Action will be performed for {label} OverTemperature Protection." , level="DEBUG")

    # Loop Method
    # Infinite Loop
    def loop(self):
        while True:
            # Get current CPU Temperatures
            cpu_temp = self.get_cpu_temperatures()

            # Print current CPU Temperature to Console
            log(f"Current CPU Temperature: {cpu_temp}°C" , level="INFO")

            # Get current RAM Temperatures
            # ...

            # Get current Chipset Temperatures
            # ...

            # Get current HBA Temperatures
            # ...

            # Get current ALL Drive Temperatures
            drives_temps_all = self.get_drives_temperatures()
            # drives_count = len(drives_temps_all)
            if drives_temps_all is not None and len(drives_temps_all) > 0:
                drives_temps_max = max(drives_temps_all)
                log(f"Maximum DRIVE Temperature: {drives_temps_max}°C" , level="INFO")
            else:
                drives_temps_max = None
                log("No DRIVE Detected" , level="INFO")

            # Get current HDD Temperatures
            hdd_temps_all = self.get_drives_temperatures(filterType = DiskType.HDD)
            # hdd_count = len(hdd_temps_all)
            if hdd_temps_all is not None and len(hdd_temps_all) > 0:
                hdd_temps_max = max(hdd_temps_all)
                log(f"Maximum HDD Temperature: {hdd_temps_max}°C" , level="INFO")
            else:
                hdd_temps_max = None
                log("No HDD Detected" , level="INFO")

            # Get current SSD Temperatures
            ssd_temps_all = self.get_drives_temperatures(filterType = DiskType.SSD)
            # ssd_count = len(ssd_temps_all)
            if ssd_temps_all is not None and len(ssd_temps_all) > 0:
                ssd_temps_max = max(ssd_temps_all)
                log(f"Maximum SSD Temperature: {ssd_temps_max}°C" , level="INFO")
            else:
                ssd_temps_max = None
                log("No SSD Detected" , level="INFO")

            # Get current NVME Temperatures
            nvme_temps_all = self.get_drives_temperatures(filterType = DiskType.NVME)
            # nvme_count = len(nvme_temps_all)
            if nvme_temps_all is not None and len(nvme_temps_all) > 0:
                nvme_temps_max = max(nvme_temps_all)
                log(f"Maximum NVME Temperature: {nvme_temps_max}°C" , level="INFO")
            else:
                nvme_temps_max = None
                log("No NVME Detected" , level="INFO")

            # Initialize new_fan_speed = current_fan_speed
            new_fan_speed_cpu = current_fan_speed
            new_fan_speed_drive = current_fan_speed
            new_fan_speed_hdd = current_fan_speed
            new_fan_speed_ssd = current_fan_speed
            new_fan_speed_nvme = current_fan_speed

            # Protect CPU Temperature
            # TO_BE_IMPLEMENTED

            # Regulate Fan Speed based on CPU Temperature
            new_fan_speed_cpu = self.run_temperature_controller(label = "CPU" , id = "cpu" , current_temp = cpu_temp , current_fan_speed = new_fan_speed_cpu)



            # Protect Drives Temperature
            self.run_temperature_protection(label = "DRIVE" , id = "drive" , current_temp = drives_temps_max)

            # Regulate Fan Speed based on Drives Temperature
            new_fan_speed_drive = self.run_temperature_controller(label = "Drive" , id = "drive" , current_temp = drives_temps_max , current_fan_speed = new_fan_speed_drive)



            # Protect HDD Temperature
            self.run_temperature_protection(label = "HDD" , id = "hdd" , current_temp = hdd_temps_max)

            # Regulate Fan Speed based on HDD Temperature
            new_fan_speed_hdd = self.run_temperature_controller(label = "HDD" , id = "hdd" , current_temp = hdd_temps_max , current_fan_speed = new_fan_speed_hdd)



            # Protect SSD Temperature
            self.run_temperature_protection(label = "SSD" , id = "ssd" , current_temp = ssd_temps_max)

            # Regulate Fan Speed based on SSD Temperature
            new_fan_speed_ssd = self.run_temperature_controller(label = "SSD" , id = "ssd" , current_temp = ssd_temps_max , current_fan_speed = new_fan_speed_ssd)



            # Protect NVME Temperature
            self.run_temperature_protection(label = "NVME" , id = "nvme" , current_temp = nvme_temps_max)

            # Regulate Fan Speed based on NVME Temperature
            new_fan_speed_nvme = self.run_temperature_controller(label = "NVME" , id = "nvme" , current_temp = nvme_temps_max , current_fan_speed = new_fan_speed_nvme)




            # Get worst Case
            #new_fan_speed = max([new_fan_speed_cpu , new_fan_speed_drive])
            new_fan_speed = max([new_fan_speed_cpu , new_fan_speed_drive , new_fan_speed_hdd , new_fan_speed_ssd , new_fan_speed_nvme])

            # Set Fan Speed
            if new_fan_speed != current_fan_speed:
                # Echo
                log(f"Fan Controller: Updating Fan Speed from {current_fan_speed}% to {new_fan_speed}%." , level="INFO")

                # Update
                self.set_fan_speed(new_fan_speed)
            else:
                # Echo
                log(f"Fan Controller: No Fan Speed Update required. Keeping Fan Speed to {current_fan_speed}% but sending Reference Again." , level="DEBUG")

                # Prevent e.g. (external) manual testing from "blocking" the Fan Speed to a Low Value in case Fan Speed is already at 100%
                self.set_fan_speed(new_fan_speed)

            # Get and Log Current Fan Speed
            self.get_fan_speeds()

            # Get and Log IPMI System Event Log
            try:
                self.get_system_event_log()
            except Exception as e:
                log(f"Event Log: Error Parsing the IPMI Event Log. Error was: {e}." , level="ERROR")

            # Wait UPDATE_INTERVAL seconds before checking the temperature again
            #pprint.pprint(global_data.config)
            time.sleep(global_data.config["general"]["update_interval"])


    def set_fan_mode_full(self) -> None:
        # Echo
        log("Setting Fan Control Mode to Full (Manual)" , level="INFO")

        # IPMI tool command to set the fan control mode to manual (Full)
        fan_speed_full = global_data.config["ipmi"]["fan_modes"]["full"]["registers"]
        cmd = ["ipmitool" , "raw"] + fan_speed_full
        Command(command = cmd , return_result = False , check_return_code = True)
        time.sleep(2)

    def set_fan_mode_optimal(self) -> None:
        # Echo
        log("Setting Fan Control Mode to Optimal", level="INFO")
        log("This is needed because in some cases the Fan Speed is stuck, if already starting in Full Mode", level="INFO")

        # IPMI tool command to set the fan control mode to Optimal
        fan_speed_optimal = global_data.config["ipmi"]["fan_modes"]["optimal"]["registers"]
        cmd = ["ipmitool" , "raw"] + fan_speed_optimal
        Command(command = cmd , return_result = False , check_return_code = True)
        time.sleep(2)

    def set_fan_mode(self) -> None:
        # Setting Fan Control Mode to Optimal
        # This is needed because in some cases the Fan Speed is stuck, if already starting in Full Mode
        self.set_fan_mode_optimal()

        # Setting Fan Control Mode to Full (Manual)
        self.set_fan_mode_full()

    def configure(self):
        # Allow Function to modify global_data.config Global Variable
        # global global_data.config

        # Get Configuration Folder
        SUPERMICRO_FAN_CONTROL_CONFIG_PATH = os.getenv("SUPERMICRO_FAN_CONTROL_CONFIG_PATH")

        if SUPERMICRO_FAN_CONTROL_CONFIG_PATH is None:
            SUPERMICRO_FAN_CONTROL_CONFIG_PATH = "/etc/supermicro-fan-control/"

        # Echo
        log(f"Using Configuration Folder {SUPERMICRO_FAN_CONTROL_CONFIG_PATH}" , level="INFO")

        # Read General Configuration
        self.read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/settings.yml.default")
        self.read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/settings.yml")

        # Print Configuration
        # pprint.pprint(CONFIG)
        # print(json.dumps(CONFIG, indent=4, sort_keys=True))

        # Extract Configuration Variables
        general = global_data.config['general']
        motherboard = general['motherboard']

        # Read IPMI Configuration
        self.read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/ipmi.d/default.yml")
        self.read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/ipmi.d/{motherboard}.yml")

        # Print Configuration
        # pprint.pprint(CONFIG)
        # print(json.dumps(CONFIG, indent=4, sort_keys=True))

        # Set fan Mode
        self.set_fan_mode()

        # Set the Correct Environment Variables
        for name in global_data.config["general"]["environment"]:
            # Get Value
            value = str(global_data.config["general"]["environment"][name])

            # Echo
            log(f"Environment: Set Environment Parameter {name} to {value}" , level="INFO")

            # Set the Variable
            os.environ[name] = value

        # Set Log Level
        globals.LOG_LEVEL = global_data.config["log"]["level"]
        log(f"Set LOG_LEVEL to {globals.LOG_LEVEL}" , level="DEBUG")
        #os.environ['LOG_LEVEL'] = LOG_LEVEL
        #print(f"SET CONFIGURED LOG_LEVEL = {LOG_LEVEL}")


@api.get("/config",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def get_config():
    return global_data.config


@api.get("/temperatures",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def get_temperatures():
    return global_data.temperature_readings


@api.get("/temperatures/cpu",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def get_temperatures_cpu():
    return global_data.temperature_readings.get("cpu")


@api.get("/temperatures/hdd",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def get_temperatures_hdd():
    return global_data.temperature_readings.get("hdd")


@api.get("/temperatures/ssd",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def get_temperatures_ssd():
    return global_data.temperature_readings.get("ssd")


@api.get("/temperatures/nvme",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def get_temperatures_nvme():
    return global_data.temperature_readings.get("nvme")


@api.get("/fans",
         summary="Query Fans Speeds",
         description="Returns Information about Fans Speeds",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def get_fan_speeds():
    return global_data.fan_speed_readings


@api.get("/event-log",
         summary="Query System Event Log",
         description="Returns BMC System Event Log",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def get_event_log():
    return global_data.bmc_event_log


def start_server():
    HTTP_BIND_HOST = global_data.config.get("web_server", {}).get("bind_address", "127.0.0.1")
    HTTP_BIND_PORT = global_data.config.get("web_server", {}).get("bind_port", 8080)
    # Get the folder where app.py actually lives
    # APP_DIR = os.path.dirname(os.path.abspath(__file__))
    # log(f"Set APP_DIR to {APP_DIR} for uvicorn")

    # Setting reload to False stops the child process loop collision, since we launch uvicorn from inside Python Application
    config = uvicorn.Config(app=api,
                            host=HTTP_BIND_HOST,
                            port=HTTP_BIND_PORT,
                            reload=False,
                            )

    server = uvicorn.Server(config)
    server.run()

def start_controller():
    # Initialize Global Controller
    global_controller = GlobalController()

    # Initialize
    global_controller.init()

    # Configure
    global_controller.configure()

    # # Launch Uvicorn on a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Override the initial Setting for current_fan_speed in case global_data.config["fan"]["min_speed"] is higher
    if "initial_speed" in global_data.config["fan"]:
        # Use the "initial_speed" Parameter or the Default Initial Value of current_fan_speed (50%), whichever is higher
        current_fan_speed = max(default_initial_fan_speed , global_data.config["fan"]["initial_speed"])
    else:
        # Use the "min_speed" Parameter or the Default Initial Value of current_fan_speed (50%), whichever is higher
        current_fan_speed = max(default_initial_fan_speed , global_data.config["fan"]["min_speed"])

    # Set initial minimum fan speed
    log(f"Set Initial Fan Speed to {current_fan_speed}%" , "INFO")
    global_controller.set_fan_speed(current_fan_speed)

    # Run Control Loop
    global_controller.loop()

def stop_controller():
    pass


# Main Method
if __name__ == "__main__":
    # Parse Command line Arguments
    parser = argparse.ArgumentParser(description='Supermicro Fan Control.')
    parser.add_argument("operation")

    # Parse
    args = parser.parse_args()

    log(f"Parsed CLI Arguments: operation={args.operation}")
    log(f"Parsed CLI Arguments: {args}")


    if args.operation == "start":
        start_controller()
    elif args.operation == "stop":
        stop_controller()
