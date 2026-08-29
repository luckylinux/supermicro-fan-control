#!/usr/bin/env python3

# Core Libraries
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Path, status
from fastapi.security import OpenIdConnect
from pydantic import BaseModel, Field

import os
import sys

import datetime

import traceback
#def global_crash_reporter(exctype, value, tb):
#    """Intercepts any unhandled crash and violently forces it into stdout."""
#    # 1. Convert the hidden stack trace into a raw string
#    trace_string = "".join(traceback.format_exception(exctype, value, tb))
#
#    # 2. Print it to standard output bypassing all custom logging configs
#    print("\n!!! GLOBAL CRASH CAPTURED !!!")
#    print(trace_string)
#    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
#
#    # 3. Force systemd/journalctl to read it immediately
#    sys.stdout.flush()

# import faulthandler

# Force an immediate, low-level stack dump to standard output on any fault
# faulthandler.enable()


# Overwrite Python's default error reporter with our sledgehammer handler
# sys.excepthook = global_crash_reporter


import uvicorn
import threading

# import subprocess
import time
# import syslog
import re
# import math
import csv
import argparse

# Use Python built-in logging library
import logging

# Python Modules to interact with YAML Files
import yaml
from yaml.loader import SafeLoader

# Python Pretty Print Module
import pprint

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
from misc.logging import log_critical, log_error, log_warning, log_info, log_debug
from misc.deep_merge import deep_merge_dicts, deep_merge_lists
from misc.datatypes import isint, isfloat, float_or_none, int_or_none

# Attempt to import AMDGPU
try:
    print("Start Import amdgpu")
    import gpu.amd as amdgpu
    print("End Import amdgpu", flush=True)
except Exception as e:
    print("Error occurred when loading AMDGPU.", flush=True)
    print(f"Error was: {e}", flush=True)
    amdgpu = None

# Define LOG_LEVEL
# LOG_LEVEL = LogLevel.DEBUG

# Initialize minimum Fan Speed to 50%
# Will be overridden by fan_controller_config["initial_speed"] in case that Value is Higher than this
default_initial_fan_speed = 50 # [%] Current Fan Speed

class Data:
    # Declare Attributes
    config: dict
    temperature_readings: dict
    voltages_readings: dict
    fan_speed_readings: dict
    fan_speed_references: dict
    bmc_event_log: list
    bmc_sensors_readings: dict

    # Class Constructor
    def __init__(self) -> None:
        # Initialize Configuration
        self.config = {}

        # Initialize Temperatures Readings
        self.temperature_readings = {}

        # Initialize Voltages Readings
        self.voltages_readings = {}

        # Initialize Fan Speed Readings
        self.fan_speed_readings = {}

        # Initialize Fan Speed References
        self.fan_speed_references = {}

        # Initialize BMC Sensors Readings
        self.bmc_sensors_readings = {}

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
        log_debug("Previous Configuration:")
        log_debug(json.dumps(global_data.config,
                             indent=4,
                             sort_keys=True
                             )
                 )

        # Echo
        log_debug("Merging Configuration:")

        # Deep Merge Configuration
        deep_merge_dicts(config, config_b)

        # Display Updated Configuration
        log_debug("New Configuration:")
        log_debug(json.dumps(global_data.config,
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
            log_info(f"Loading File {filepath}")

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
                    log_warning(f"File {filepath} is empty")
        else:
            # Echo
            log_warning(f"File {filepath} does NOT exist")

    # Get the current HDD/SSD/NVME Temperature(s)
    def get_drives_temperatures(self,
                                filterType = None
                                ) -> list | None:

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
            driveTypeStr = "all"

        # Debug
        log_debug(f"Get Drives Temperatures for Type {driveTypeStr}")

        # Initialize Array
        temps = []
        drives = {}

        # Initialize Global Dictionary if needed
        if "drives" not in  global_data.temperature_readings:
            global_data.temperature_readings["drives"] = {}

        # Check all Disks
        di = DiskInfo()
        disks = di.get_disk_list(sorting=True)

        diskinfo_logger = logging.getLogger("diskinfo")

        diskinfo_log_level_str = global_data.config.get("log", {}).get("diskinfo", {}).get("general", "INFO")
        diskinfo_log_level_obj = logging.getLevelName(diskinfo_log_level_str.upper())
        diskinfo_logger.setLevel(diskinfo_log_level_obj)

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
                    log_info(f"{driveTypeStr} Drive {filteredid} has Temperature = {temp}°C")

                    # Add to Array
                    temps.append(temp)

                    # Add to Dictionary
                    drives.update({filteredid: temp})

        # global_data.temperature_readings["drives"]["avg"] = avg_cpu_temp
        # global_data.temperature_readings["drives"]["min"] = max_cpu_temp
        # global_data.temperature_readings["drives"]["max"] = min_cpu_temp
        # global_data.temperature_readings["drives"]["details"] = temps

        drives_dict = {}
        if len(temps) > 0:
            drives_dict["avg"] = sum(temps) / len(temps)
            drives_dict["max"] = max(temps)
            drives_dict["min"] = min(temps)

        drives_dict["details"] = drives

        global_data.temperature_readings["drives"].update({driveTypeStr: drives_dict})

        # Return Result
        return temps

    # Get RAM Temperature(s)
    def get_ram_temperatures(self) -> list | None:

        # Debug
        log_debug(f"Get RAM Temperatures")

        # Initialize Array
        temps = []
        dimm_temperatures = {}

        # Initialize Global Dictionary if needed
        if "ram" not in  global_data.temperature_readings:
            global_data.temperature_readings["ram"] = {}

        # Check all DIMMs
        dimm_pattern = re.compile(r"^(DIMM[A-Z]+[1234]+\s+Temp)", re.IGNORECASE)
        dimm_lines = [item for item in global_data.bmc_sensors_readings.get("lines", []) if dimm_pattern.match(item)]

        if dimm_lines:
            reader = csv.reader(dimm_lines, delimiter=',')
            for index, row in enumerate(reader):
                # Get Label
                dimm_label = row[0]

                # Get Value
                dimm_temperature = float_or_none(row[1])

                # Get Unit
                dimm_unit = row[2]

                # Get DIMM Status
                dimm_status = row[3]

                # Lower Non-Recoverable (LNR)
                dimm_lnr = float_or_none(row[4])

                # Lower Critical (LC)
                dimm_lc = float_or_none(row[5])

                # Lower Non-Critical (LNC)
                dimm_lnc = float_or_none(row[6])

                # Upper Non-Critical (UNC)
                dimm_unc = float_or_none(row[7])

                # Upper Critical (UC)
                dimm_uc = float_or_none(row[8])

                # Upper Non-Recoverable (UNR)
                dimm_unr = float_or_none(row[9])

                # If Speed is a valid Number
                # if isfloat(fan_value) is True:
                if dimm_temperature is not None:
                    # fan_speed_number = float(fan_value)
                    # if not math.isnan(number) and not math.isinf(number):
                    log_debug(f"Current {dimm_label} Temperature: {dimm_temperature} {dimm_unit}")

                    # Add to Array
                    temps.append(dimm_temperature)
                # else:
                #     fan_speed_number = None

                # Initialize Dictionary
                dimm_dict = {}
                dimm_dict["id"] = dimm_label
                dimm_dict["temperature"] = dimm_temperature
                dimm_dict["unit"] = dimm_unit
                dimm_dict["status"] = dimm_status
                dimm_dict["lower_non_recoverable"] = dimm_lnr
                dimm_dict["lower_critical"] = dimm_lc
                dimm_dict["lower_non_critical"] = dimm_lnc
                dimm_dict["upper_non_critical"] = dimm_unc
                dimm_dict["upper_critical"] = dimm_uc
                dimm_dict["upper_non_recoverable"] = dimm_unr

                # Add to Dictionary
                dimm_temperatures.update({dimm_label: dimm_dict})

        ram_dict = {}
        if len(temps) > 0:
            ram_dict["avg"] = sum(temps) / len(temps)
            ram_dict["max"] = max(temps)
            ram_dict["min"] = min(temps)

        ram_dict["details"] = dimm_temperatures

        global_data.temperature_readings["ram"].update(ram_dict)

        # Return Result
        return temps


    # Get the current PCH Temperature(s)
    def get_pch_temperatures(self) -> float | int | None:
        # Initialize Array
        temps = []
        pch_temperatures = {}

        # Debug
        log_debug(f"Get PCH Temperatures")

        # Initialize Global Dictionary if needed
        if "pch" not in  global_data.temperature_readings:
            global_data.temperature_readings["pch"] = {}

        # Check PCH
        pch_pattern = re.compile(r"^(PCH\s+Temp)", re.IGNORECASE)
        pch_lines = [item for item in global_data.bmc_sensors_readings.get("lines", []) if pch_pattern.match(item)]

        if pch_lines:
            reader = csv.reader(pch_lines, delimiter=',')
            for index, row in enumerate(reader):
                # Get Label
                pch_label = row[0]

                # Get Value
                pch_temperature = float_or_none(row[1])

                # Get Unit
                pch_unit = row[2]

                # Get DIMM Status
                pch_status = row[3]

                # Lower Non-Recoverable (LNR)
                pch_lnr = float_or_none(row[4])

                # Lower Critical (LC)
                pch_lc = float_or_none(row[5])

                # Lower Non-Critical (LNC)
                pch_lnc = float_or_none(row[6])

                # Upper Non-Critical (UNC)
                pch_unc = float_or_none(row[7])

                # Upper Critical (UC)
                pch_uc = float_or_none(row[8])

                # Upper Non-Recoverable (UNR)
                pch_unr = float_or_none(row[9])

                # If Speed is a valid Number
                # if isfloat(fan_value) is True:
                if pch_temperature is not None:
                    # fan_speed_number = float(fan_value)
                    # if not math.isnan(number) and not math.isinf(number):
                    # log_info(f"Current {pch_label} (Temperature): {pch_temperature} {pch_unit}")

                    # Add to Array
                    temps.append(pch_temperature)
                # else:
                #     fan_speed_number = None

                # Initialize Dictionary
                pch_dict = {}
                pch_dict["id"] = pch_label
                pch_dict["temperature"] = pch_temperature
                pch_dict["unit"] = pch_unit
                pch_dict["status"] = pch_status
                pch_dict["lower_non_recoverable"] = pch_lnr
                pch_dict["lower_critical"] = pch_lc
                pch_dict["lower_non_critical"] = pch_lnc
                pch_dict["upper_non_critical"] = pch_unc
                pch_dict["upper_critical"] = pch_uc
                pch_dict["upper_non_recoverable"] = pch_unr

                # Add to Dictionary
                pch_temperatures.update({pch_label: pch_dict})

               # if temp is not None:
               #     if driveType == filterType or filterType is None:
               #         # Echo
               #        log_debug(f"{driveTypeStr} RAM DIMM {filteredid} has Temperature = {temp}°C")
               #         # Add to Array
               #         temps.append(temp)
               #
               #        # Add to Dictionary
               #        drives.update({filteredid: temp})

        pch_dict = {}
        if len(temps) > 0:
            pch_dict["avg"] = sum(temps) / len(temps)
            pch_dict["max"] = max(temps)
            pch_dict["min"] = min(temps)

        pch_dict["details"] = pch_temperatures

        global_data.temperature_readings["pch"].update(pch_dict)

        # Return Result
        return temps

    # Get the current NIC Temperature(s)
    def get_nic_temperatures(self) -> float | int | None:
        # Debug
        log_debug(f"Get NIC Temperatures")

        # Dummy Value for now
        return 50.0

    # Get the current GPU Temperature(s)
    def get_gpu_temperatures(self) -> float | int | None:
        # Debug
        log_debug(f"Get GPU Temperatures")

        # Initialize Global Dictionary if needed
        if "gpu" not in global_data.temperature_readings:
            global_data.temperature_readings["gpu"] = {}

        # Initialize Variables
        nvidia_gpu_temperatures = []
        amd_gpu_temperatures = []
        intel_gpu_temperatures = []

        # Get NVIDIA GPUs
        # ...
        nvidia_gpu_temperature_max = None
        nvidia_gpu_temperature_min = None
        nvidia_gpu_temperature_avg = None

        # Get AMD GPUs Temperatures
        if amdgpu is not None:
        # if True is False:
            try:
                # print("TEST TEST", flush=True)
                amdgpu_obj = amdgpu.AMDGPU()
                # print("TEST TEST", flush=True)
                amd_gpu_temperatures = amdgpu_obj.get_temperatures()

                # Debug
                # pprint.pprint(amd_gpu_temperatures)

                amd_gpu_temperatures_array_max = [s.get("temperatures", {}).get("max", 999) for s in amd_gpu_temperatures]
                amd_gpu_temperatures_array_min= [s.get("temperatures", {}).get("min", 999) for s in amd_gpu_temperatures]
                amd_gpu_temperatures_array_avg = [s.get("temperatures", {}).get("avg", 999) for s in amd_gpu_temperatures]

                # Debug
                # pprint.pprint(amd_gpu_temperatures_array_max)
                # pprint.pprint(amd_gpu_temperatures_array_min)
                # pprint.pprint(amd_gpu_temperatures_array_avg)

                if len(amd_gpu_temperatures_array_avg) > 0:
                    amd_gpu_temperature_avg = sum(amd_gpu_temperatures_array_avg) / len(amd_gpu_temperatures_array_avg)

                if len(amd_gpu_temperatures_array_max) > 0:
                    amd_gpu_temperature_max = max(amd_gpu_temperatures_array_max, default=999)

                if len(amd_gpu_temperatures_array_min) > 0:
                    amd_gpu_temperature_min = min(amd_gpu_temperatures_array_min, default=999)
            except Exception as e:
                log_error("Error occurred while retrieving GPU Temperatures",
                          exc_info=True
                          )
        else:
            # Default Values
            amd_gpu_temperature_max = 999
            amd_gpu_temperature_min = 999
            amd_gpu_temperature_avg = 999

        # Get Intel GPUs Temperatures
        # ...
        intel_gpu_temperature_max = None
        intel_gpu_temperature_min = None
        intel_gpu_temperature_avg = None

        # Define GPU Dictionary
        gpu_dict = {}
        gpu_dict["all"] = {}
        gpu_dict["amd"] = {}
        gpu_dict["nvidia"] = {}
        gpu_dict["intel"] = {}

        amd_dict = {}
        amd_dict["max"] = amd_gpu_temperature_max
        amd_dict["min"] = amd_gpu_temperature_min
        amd_dict["avg"] = amd_gpu_temperature_avg
        amd_dict["details"] = amd_gpu_temperatures

        all_dict = {}

        # Add Valid Elements to arrays
        all_gpu_temperature_max = []
        all_gpu_temperature_min = []
        all_gpu_temperature_avg = []

        if intel_gpu_temperature_max is not None:
            all_gpu_temperature_max.append(intel_gpu_temperature_max)
        if nvidia_gpu_temperature_max is not None:
            all_gpu_temperature_max.append(nvidia_gpu_temperature_max)
        if amd_gpu_temperature_max is not None:
            all_gpu_temperature_max.append(amd_gpu_temperature_max)

        if intel_gpu_temperature_min is not None:
            all_gpu_temperature_min.append(intel_gpu_temperature_min)
        if nvidia_gpu_temperature_min is not None:
            all_gpu_temperature_min.append(nvidia_gpu_temperature_min)
        if amd_gpu_temperature_min is not None:
            all_gpu_temperature_min.append(amd_gpu_temperature_min)

        if intel_gpu_temperature_avg is not None:
            all_gpu_temperature_avg.append(intel_gpu_temperature_avg)
        if nvidia_gpu_temperature_avg is not None:
            all_gpu_temperature_avg.append(nvidia_gpu_temperature_avg)
        if amd_gpu_temperature_avg is not None:
            all_gpu_temperature_avg.append(amd_gpu_temperature_avg)

        # if len(amd_gpu_temperature_max) > 0:
        all_dict["max"] = max(all_gpu_temperature_max)

        # if len(amd_gpu_temperature_min) > 0:
        all_dict["min"] = min(all_gpu_temperature_min)

        # if len(amd_gpu_temperature_avg) > 0:
        all_dict["avg"] = sum(all_gpu_temperature_avg) / len(all_gpu_temperature_avg)

        gpu_dict["all"] = all_dict
        gpu_dict["amd"] = amd_dict

        global_data.temperature_readings["gpu"] = gpu_dict

        # Return Maximum
        if len(all_gpu_temperature_max) > 0:
            return max([all_gpu_temperature_max], default=999)
        else:
            # Dummy Value for now
            return 99.9

    # Get the current CPU Temperature(s)
    def get_cpu_temperatures(self) -> float | int | None:
        # Debug
        log_debug(f"Get CPU Temperatures")

        # Initialize cpu_temps and core_temps to Empty Array
        cpu_temps = []
        core_temps = []

        # Get PCU Sensor Driver Configuration
        cpu_driver = global_data.config.get("cpu", {}).get("driver", "ipmi")

        # Check which Driver to Use
        if cpu_driver == "ipmi":
            # Debug
            log_debug(f"Extracting CPU Temperatures Data using ipmitool Driver (cpu driver Setting in Configuration: {cpu_driver})")

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
                log_error("Failed to retrieve CPU temperature using ipmitool.")
                return None
        else:
            # Debug
            log_debug(f"Extracting CPU Temperatures Data using psutil Driver (cpu driver Setting in Configuration: {cpu_driver})")

            # Use psutil Python Library to access Data Locally
            temperatures = psutil.sensors_temperatures()

            # Debug
            # pprint.pprint(temperatures)

            # Extract CPU Temperatures
            cpu_temperatures_all = temperatures.get(cpu_driver)

            if cpu_temperatures_all:
                # Extract CPUs and Cores Temperatures
                if cpu_driver == "coretemp":
                    cpu_temps = [int(item.current) for item in cpu_temperatures_all if "Package id" in item.label]
                    core_temps = [int(item.current) for item in cpu_temperatures_all if "Core" in item.label]
                elif cpu_driver == "k10temp":
                    cpu_temps = [int(item.current) for item in cpu_temperatures_all if "Tctl" in item.label]
                    core_temps = [int(item.current) for item in cpu_temperatures_all if "Tccd" in item.label]
                else:
                    # Just use as it is, at least we have the information we need, even though it might not be structured correctly
                    cpu_temps = [int(item.current) for item in cpu_temperatures_all]
                    core_temps = [int(item.current) for item in cpu_temperatures_all]
            else:
                log_error("Failed to retrieve CPU temperature using psutil.")
                return None

        # Common Code
        # Data has already been extracted but can be processed in the same Way

        # Number of CPUs Detected on the System
        NCPUs = len(cpu_temps)

        # Log how many CPUs were Detected
        log_debug(f"Number of CPUs Detected on this System: {NCPUs}")

        # Print individual CPU Temperatures
        for cpu_index , cpu_temp in enumerate(cpu_temps):
            log_debug(f"Current Temperatures of CPU {cpu_index}: {cpu_temp}")

        # Print individual Core Temperatures (if available)
        if len(core_temps) > 0:
            for core_index , core_temp in enumerate(core_temps):
               log_debug(f"Current Temperatures of Core/CCD {core_index}: {core_temp}")

        # Calculate Average/Maximum Temperature between CPUs
        if len(cpu_temps) > 0:
            avg_cpu_temp = sum(cpu_temps) / len(cpu_temps)
            max_cpu_temp = max(cpu_temps) / 1.0
            min_cpu_temp = min(cpu_temps) / 1.0
        else:
            avg_cpu_temp = 99.9
            max_cpu_temp = 99.9
            min_cpu_temp = 99.9

        # Print Average / Maximum Value
        log_debug(f"Average CPU temperature: {avg_cpu_temp}°C")
        log_debug(f"Maximum CPU temperature: {max_cpu_temp}°C")

        # Create Structure to store Data
        details_data = dict()
        details_data["package"] = cpu_temps
        details_data["cores"] = core_temps

        # Store in Global Dictionary
        global_data.temperature_readings["cpu"] = {}
        global_data.temperature_readings["cpu"]["avg"] = avg_cpu_temp
        global_data.temperature_readings["cpu"]["min"] = max_cpu_temp
        global_data.temperature_readings["cpu"]["max"] = min_cpu_temp

        global_data.temperature_readings["cpu"]["details"] = details_data

        # Return one Value
        return max_cpu_temp


    # Get the System Event Log(s) filtered
    def get_system_event_log_filtered(self,
                                      filter: str = "",
                                      label: str = ""
                                      ) -> None | Command:

        if global_data.config.get("ipmi", {}).get("enabled", False) is True:
            # Check if any Events occurred at all
            cmd = [["ipmitool" , "-c" , "sel"] , ["grep" , "-i" , "Entries"] , ["sed" , "-E" , "'s|^Entries\\s*?:\\s*?([0-9]*)$|\\1|'"]]
            events_obj = Command(command = cmd , return_result = True , check_return_code = True , debug = global_data.config["general"]["debug"])
            time.sleep(5)
            has_events = events_obj.getOutput(decode = True)

            # Initialize as None by Default
            system_event_log_obj = None

            # Echo
            log_debug(f"System Event Log [{label}]: Checking if System had any Events Logged")

            # Only get System Event Log if there are Events registered, otherwise we'll have Errors later
            if has_events is not None and len(has_events) > 0:
                # If a multi-line Output is returned, just grab the first Line
                has_events_split = has_events.split("\n")
                if isinstance(has_events_split , list):
                    events = has_events_split[0]
                else:
                    events = has_events_split

                # Echo
                log_debug(f"System Event Log [{label}]: {events} (RAW) Events have been Logged")

                if isint(events):
                    # Get Number of Event
                    Nevents = int(events)

                    if Nevents > 0:
                        # Echo
                        log_debug(f"System Event Log [{label}]: {Nevents} (Numeric) Events have been Logged")

                        # Get System Events according to Filter
                        cmd = [["ipmitool" , "-c" , "sel" , "elist"] , ["grep" , "-Ei" , f"'{filter}'"]]
                        system_event_log_obj = Command(command = cmd , check_return_code = False , return_result = True , debug = global_data.config["general"]["debug"])
                        time.sleep(2)
                    else:
                        # Echo
                        log_debug(f"System Event Log [{label}]: System Log is Empty")
                else:
                    # Echo
                    log_debug(f"System Event Log [{label}]: Invalid Response Received (non-Integer Data) -> {events}")

            else:
                # Echo
                log_debug(f"System Event Log [{label}]: Command returned None or Zero-Length")

            # Return Output
            return system_event_log_obj

    # Get the System Event Log(s)
    def get_system_event_log(self,
                             log_all: bool = True,
                             log_fans: bool = True,
                             log_temperatures: bool = True
                             ) -> list[dict]:
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
                    log_warning(f"System Event Log [{system_event_type}]: [{event_component}] Event ID {event_id} on {event_date} at {event_time}: {event_message} (Threshold: {event_threshold} , Action: {event_action})")

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
            log_info(f"System Event Log [{system_event_type}]: Please Fix the Problem for Type {system_event_type} then clear the System Event Log !")

        # If no Entries exist in the System Event Log
        else:
            # Echo
            log_debug(f"System Event Log [{system_event_type}]: no Entries matching Type {system_event_type} exist in the System Event Log.")

        # Save in Global Data
        global_data.bmc_event_log = events

    # Get bmc Sensor(s)
    def get_bmc_sensors(self):
        if global_data.config.get("ipmi", {}).get("enabled", False) is True:
            cmd = [["ipmitool" , "-c" , "sensor"]]
            sensor_obj = Command(command = cmd , return_result = True , check_return_code = True)
            time.sleep(2)
            sensor_lines = sensor_obj.getOutput(decode=True)

            sensors_data_lines = []
            sensors_data_array = []

            if sensor_lines:
                # Save the Line as it is
                sensor_lines_split = sensor_lines.split('\n')
                sensors_data_lines = sensor_lines_split

                # Transform into a Structured Form
                reader = csv.reader(sensor_lines.split('\n'), delimiter=',')

                for row in reader:
                    # If Array is NOT empty
                    if row is not None and len(row) > 0:
                        sensors_data_array.append(row)

            # Add to Global Data
            current_time = datetime.datetime.now()
            global_data.bmc_sensors_readings["time"] = current_time
            global_data.bmc_sensors_readings["timestamp"] = current_time.timestamp()
            global_data.bmc_sensors_readings["lines"] = sensors_data_lines
            global_data.bmc_sensors_readings["array"] = sensors_data_array

            # Debug
            # pprint.pprint(sensors_data_lines)

    # Get the current Fan Speed(s)
    def get_fan_speeds(self):
        if global_data.config.get("ipmi", {}).get("enabled", False) is True:
            self.ipmi_get_fan_speeds()

    # Get the current Voltage(s)
    def get_voltages(self):
        if global_data.config.get("ipmi", {}).get("enabled", False) is True:
            self.ipmi_get_voltages()

    # Get the current Fan Speed(s) using IPMI
    def ipmi_get_fan_speeds(self):
        # cmd = [["ipmitool" , "-c" , "sensor"] , ["grep" , "-Ei" , "'^FAN|^MB-FAN|^BPN-FAN'"]]
        # fan_speed_obj = Command(command = cmd , return_result = True , check_return_code = True)
        # time.sleep(2)
        # fan_speed_lines = fan_speed_obj.getOutput(decode=True)

        # Compile the case-insensitive regular expression pattern
        fan_pattern = re.compile(r"^(FAN|MB-FAN|BPN-FAN)", re.IGNORECASE)
        fan_speed_lines = [item for item in global_data.bmc_sensors_readings.get("lines", []) if fan_pattern.match(item)]

        # Debug
        # pprint.pprint(fan_speed_lines)

        fan_speeds = {}

        if fan_speed_lines:
            #for fan_speed in fan_speed_lines:
            #    print(f"Fan Speed: {fan_speed}")
            # reader = csv.reader(fan_speed_lines.split('\n'), delimiter=',')
            reader = csv.reader(fan_speed_lines, delimiter=',')
            for index, row in enumerate(reader):
                # If Array is NOT empty
                if row is not None and len(row) > 0:
                    # Get Label
                    fan_label = row[0]

                    # Get Value
                    fan_speed = float_or_none(row[1])

                    # Get Measurement Unit
                    fan_unit = row[2]

                    # Get Fan Status
                    fan_status = row[3]

                    # Lower Non-Recoverable (LNR)
                    fan_lnr = float_or_none(row[4])

                    # Lower Critical (LC)
                    fan_lc = float_or_none(row[5])

                    # Lower Non-Critical (LNC)
                    fan_lnc = float_or_none(row[6])

                    # Upper Non-Critical (UNC)
                    fan_unc = float_or_none(row[7])

                    # Upper Critical (UC)
                    fan_uc = float_or_none(row[8])

                    # Upper Non-Recoverable (UNR)
                    fan_unr = float_or_none(row[9])

                    # If Speed is a valid Number
                    # if isfloat(fan_value) is True:
                    if fan_speed is not None:
                        # fan_speed_number = float(fan_value)
                        # if not math.isnan(number) and not math.isinf(number):
                        log_info(f"Current {fan_label} Fan Speed: {fan_speed} rpm")
                    # else:
                    #     fan_speed_number = None

                    # Initialize Dictionary
                    fan_dict = {}
                    fan_dict["id"] = fan_label
                    fan_dict["speed"] = fan_speed
                    fan_dict["unit"] = fan_unit
                    fan_dict["status"] = fan_status
                    fan_dict["lower_non_recoverable"] = fan_lnr
                    fan_dict["lower_critical"] = fan_lc
                    fan_dict["lower_non_critical"] = fan_lnc
                    fan_dict["upper_non_critical"] = fan_unc
                    fan_dict["upper_critical"] = fan_uc
                    fan_dict["upper_non_recoverable"] = fan_unr

                    # Add to Dictionary
                    fan_speeds.update({fan_label: fan_dict})

            # Add to Global Data
            global_data.fan_speed_readings = fan_speeds

    # Get Voltages
    def ipmi_get_voltages(self):
        # cmd = [["ipmitool" , "-c" , "sensor"] , ["grep" , "-Ei" , "'Volts'"]]
        # voltage_obj = Command(command = cmd , return_result = True , check_return_code = True)
        # time.sleep(2)
        # voltage_lines = voltage_obj.getOutput(decode=True)

        voltages = {}

        # Compile the case-insensitive regular expression pattern
        voltage_pattern = re.compile(r"Volts", re.IGNORECASE)
        voltage_lines = [item for item in global_data.bmc_sensors_readings.get("lines", []) if voltage_pattern.match(item)]

        # Debug
        # pprint.pprint(voltage_lines)

        if voltage_lines:
            reader = csv.reader(voltage_lines, delimiter=',')
            for id, row in enumerate(reader):
                # If Array is NOT empty
                if row is not None and len(row) > 0:
                    # Get Label
                    voltage_label = row[0]

                    # Get Value
                    voltage_value = float_or_none(row[1])

                    # Get Measurement Unit
                    voltage_unit = row[2]

                    # Get Fan Status
                    voltage_status = row[3]

                    # Lower Non-Recoverable (LNR)
                    voltage_lnr = float_or_none(row[4])

                    # Lower Critical (LC)
                    voltage_lc = float_or_none(row[5])

                    # Lower Non-Critical (LNC)
                    voltage_lnc = float_or_none(row[6])

                    # Upper Non-Critical (UNC)
                    voltage_unc = float_or_none(row[7])

                    # Upper Critical (UC)
                    voltage_uc = float_or_none(row[8])

                    # Upper Non-Recoverable (UNR)
                    voltage_unr = float_or_none(row[9])

                    # If Speed is a valid Number
                    # if isfloat(fan_value) is True:
                    if voltage_value is not None:
                        # fan_speed_number = float(fan_value)
                        # if not math.isnan(number) and not math.isinf(number):
                        log_info(f"Current {voltage_label} Voltage: {voltage_value} V")
                    # else:
                    #     fan_speed_number = None

                    # Initialize Dictionary
                    voltage_dict = {}
                    voltage_dict["id"] = voltage_label
                    voltage_dict["voltage"] = voltage_value
                    voltage_dict["unit"] = voltage_unit
                    voltage_dict["status"] = voltage_status
                    voltage_dict["lower_non_recoverable"] = voltage_lnr
                    voltage_dict["lower_critical"] = voltage_lc
                    voltage_dict["lower_non_critical"] = voltage_lnc
                    voltage_dict["upper_non_critical"] = voltage_unc
                    voltage_dict["upper_critical"] = voltage_uc
                    voltage_dict["upper_non_recoverable"] = voltage_unr

                    # Add to Dictionary
                    voltages.update({voltage_label: voltage_dict})

            # Add to Global Data
            global_data.voltages_readings = voltages

    # Set the fan speed
    def set_fan_speed(self,
                      speed
                      ) -> None:
        # speed: integer between 0 and 100 (possibly further limited to fan_controller_config["min_speed"] and fan_controller_config["max_speed"])

        # Allow to update Global Variables
        global current_fan_speed

        # Set the Current Fan Speed (Reference) to the speed Input we receive
        current_fan_speed = speed

        # Debug
        log_debug(f"Set Fan Speed to {speed}")

        # Convert the speed percentage to a hex value
        # !! The 255/100 does NOT seem to be correct, at least on some Motherboards !!
        # hex_speed = format(speed * 255 // 100, "02x")

        # Convert the speed percentage to a hex value
        # Use max_speed_hex and min_speed_hex from global_data.config

        if global_data.config.get("ipmi", {}).get("enabled", False) is True:
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
                log_info(f"Fan Controller: Setting Fan Zone {fan_zone_id} ({fan_zone_description}) to {fan_zone_speed_percent}% (Decimal Speed Value {fan_zone_speed_dec}, Hex Speed Value 0x{fan_zone_speed_hex})")

                # Set the Fan Speed for Zone
                cmd = ["ipmitool" , "raw"] + fan_zone_registers + [f"0x{fan_zone_speed_hex}"]
                Command(command = cmd , return_result = False , check_return_code = True)
                time.sleep(2)

                # Log the Fan Speed change to syslog
                log_info(f"Fan Controller: Fan Zone {fan_zone_id} ({fan_zone_description}) Speed has been adjusted to {fan_zone_speed_percent}% (Decimal Speed Value {fan_zone_speed_dec}, Hex Value 0x{fan_zone_speed_hex})")


    # Run Temperature Controller
    def run_temperature_controller(self,
                                   label,
                                   id,
                                   current_temp,
                                   current_fan_speed
                                   ) -> int:

        id_splits = id.split("/")
        device_config = global_data.config
        for index, item in enumerate(id_splits):
            device_config = device_config.get(item, {})

        fan_controller_config = global_data.config["fan_controller"]

        # Debug
        # print(f"Run Temperature Controller for {id}")
        # print(f"Configuration: {device_config}")

        if current_temp is not None:
            # Initialize Variable
            new_fan_speed = current_fan_speed

            if current_temp > device_config["max_temp"] and new_fan_speed < fan_controller_config["max_speed"]:
                # Echo
                log_debug(f"{label} Temperature Controller: Increasing Fan Speed Reference since {label} Controller Temperature = {current_temp}°C is higher than the Maximum Setting = {device_config['max_temp']}°C")

                # Increase the fan speed by fan_controller_config["inc_speed_step"]% to cool down the <id>
                new_fan_speed = min(new_fan_speed + fan_controller_config["inc_speed_step"], fan_controller_config["max_speed"])

                # Echo
                log_debug(f"{label} Temperature Controller: New Fan Speed Reference based on {label} Controller Temperature: {new_fan_speed}%")

            elif current_temp < device_config["min_temp"] and new_fan_speed > fan_controller_config["min_speed"]:
                # Echo
                log_debug(f"{label} Temperature Controller: Decreasing Fan Speed Reference since {label} Temperature = {current_temp}°C is lower than the Minimum Setting = {device_config['min_temp']}°C")

                # Decrease the fan speed by fan_controller_config["dec_speed_step"]% if the temperature is below the minimum threshold
                new_fan_speed = max(new_fan_speed - fan_controller_config["dec_speed_step"], fan_controller_config["min_speed"])

                # Echo
                log_debug(f"{label} Temperature Controller: New Fan Speed Reference based on {label} Controller Temperature: {new_fan_speed}%")
            else:
                if new_fan_speed >= fan_controller_config["max_speed"]:
                    # Echo
                    log_debug(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since Current Fan Speed {current_fan_speed}% is already >= Fan Maximum Speed ({fan_controller_config['max_speed']}%)")

                elif new_fan_speed <= fan_controller_config["min_speed"]:
                    # Echo
                    log_debug(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since Current Fan Speed {current_fan_speed}% is already <= Fan Minimum Speed ({fan_controller_config['min_speed']}%)")

                if current_temp >= device_config['min_temp'] and current_temp <= device_config['max_temp']:
                    # Echo
                    log_debug(f"{label} Temperature Controller: Skipping Fan Speed Reference Update for {label} Controller since {label} Temperature = {current_temp}°C is within Histeresis Range = [{device_config['min_temp']}°C ... {device_config['max_temp']}°C]")

            # Return Result
            return new_fan_speed
        else:
            # Echo
            log_debug(f"{label} Temperature Controller: No Devices of Type {label} are installed. No Action will be performed for {label} Temperature Regulation.")

            # Return Zero
            return 0

    # Run Drives (HDD/SSD/NVME) Temperature Protection
    def run_temperature_protection(self,
                                   label,
                                   id,
                                   current_temp
                                   ) -> None:

        id_splits = id.split("/")
        device_config = global_data.config
        for index, item in enumerate(id_splits):
            device_config = device_config.get(item, {})

        fan_controller_config = global_data.config["fan_controller"]

        # Debug
        # print(f"Run Temperature Protection for {id}")
        # print(f"Configuration: {device_config}")

        if current_temp is not None:
            if current_temp >= device_config["shutdown_temp"]:
                # Echo
                log_critical(f"{label} OverTemperature Protection: Temperature = {current_temp}°C is higher than the Shutdown Setting = {device_config['shutdown_temp']}°C")
                log_critical(f"{label} OverTemperature Protection: Shutting Down System Now")

                # Wait a bit to make sure we logged everything
                time.sleep(2)

                # SHUTDOWN to prevent Damage
                os.system("shutdown -h now")
            if current_temp >= device_config["warning_temp"] and current_temp < device_config["shutdown_temp"]:
                # Echo
                log_warning(f"{label} OverTemperature Protection: Temperature = {current_temp}°C is higher than the Warning Setting = {device_config['warning_temp']}°C")
                log_warning(f"{label} OverTemperature Protection: Sounding BEEP on the Speaker")

                # BEEP Warning

                # Harcoded Values
                #os.system(f"beep -f 2500 -l 2000 -r 5 -D 1000")

                # Configurable Values
                os.system(f"beep -f {global_data.config['beep']['frequency']} -l {global_data.config['beep']['duration']} -r {global_data.config['beep']['repetitions']} -D {global_data.config['beep']['delay']}")
            elif current_temp < device_config["warning_temp"]:
                # Echo
                log_debug(f"{label} OverTemperature Protection: {label} Temperature = {current_temp}°C is lower than the {label} OverTemperature Warning Setting = {device_config['warning_temp']}°C. No Action required.")
            else:
                # Echo
                log_warning(f"{label} OverTemperature Protection: Did NOT match any IF Condition. Temperature = {current_temp}°C. {label} OverTemperature Warning Setting = {device_config['warning_temp']}°C. {label} OverTemperature Shutdown Setting = {device_config['shutdown_temp']}°C. Investigation required..")
        else:
            # Echo
            log_debug(f"{label} OverTemperature Protection: No Devices of Type {label} are installed. No Action will be performed for {label} OverTemperature Protection.")

    # Loop Method
    # Infinite Loop
    def loop(self):
        while True:
            # Get and cache all BMC Sensors
            self.get_bmc_sensors()

            # Get and Log Current Fan Speed
            self.get_fan_speeds()

            # Get and Log Voltages
            self.get_voltages()

            # Get current CPU Temperatures
            cpu_temp = self.get_cpu_temperatures()

            # Print current CPU Temperature to Console
            log_info(f"Current CPU Temperature: {cpu_temp}°C")

            # Get current RAM Temperatures
            ram_temp = self.get_ram_temperatures()

            # Print current RAM Temperature to Console
            log_info(f"Current RAM Temperature: {ram_temp}°C")

            # Get current Chipset Temperatures
            pch_temp = self.get_pch_temperatures()

            # Print current PCH Temperature to Console
            log_info(f"Current PCH Temperature: {pch_temp}°C")

            # Get current HBA Temperatures
            hba_temp = self.get_pch_temperatures()

            log_info(f"Current HBA Temperature: {hba_temp}°C")

            # Get current NIC Temperatures
            nic_temp = self.get_nic_temperatures()

            log_info(f"Current NIC Temperature: {nic_temp}°C")

            # Get current GPU Temperatures
            gpu_temp = self.get_gpu_temperatures()

            log_info(f"Current GPU Temperature: {gpu_temp}°C")

            # Get current ALL Drive Temperatures
            drives_temps_all = self.get_drives_temperatures()
            # drives_count = len(drives_temps_all)
            if drives_temps_all is not None and len(drives_temps_all) > 0:
                drives_temps_max = max(drives_temps_all)
                log_info(f"Maximum DRIVE Temperature: {drives_temps_max}°C")
            else:
                drives_temps_max = None
                log_info("No DRIVE Detected")

            # Get current HDD Temperatures
            hdd_temps_all = self.get_drives_temperatures(filterType = DiskType.HDD)
            # hdd_count = len(hdd_temps_all)
            if hdd_temps_all is not None and len(hdd_temps_all) > 0:
                hdd_temps_max = max(hdd_temps_all)
                log_info(f"Maximum HDD Temperature: {hdd_temps_max}°C")
            else:
                hdd_temps_max = None
                log_info("No HDD Detected")

            # Get current SSD Temperatures
            ssd_temps_all = self.get_drives_temperatures(filterType = DiskType.SSD)
            # ssd_count = len(ssd_temps_all)
            if ssd_temps_all is not None and len(ssd_temps_all) > 0:
                ssd_temps_max = max(ssd_temps_all)
                log_info(f"Maximum SSD Temperature: {ssd_temps_max}°C")
            else:
                ssd_temps_max = None
                log_info("No SSD Detected")

            # Get current NVME Temperatures
            nvme_temps_all = self.get_drives_temperatures(filterType = DiskType.NVME)
            # nvme_count = len(nvme_temps_all)
            if nvme_temps_all is not None and len(nvme_temps_all) > 0:
                nvme_temps_max = max(nvme_temps_all)
                log_info(f"Maximum NVME Temperature: {nvme_temps_max}°C")
            else:
                nvme_temps_max = None
                log_info("No NVME Detected")

            # Initialize new_fan_speed = current_fan_speed
            new_fan_speed_cpu = current_fan_speed
            new_fan_speed_drive = current_fan_speed
            new_fan_speed_hdd = current_fan_speed
            new_fan_speed_ssd = current_fan_speed
            new_fan_speed_nvme = current_fan_speed
            new_fan_speed_nic = current_fan_speed
            new_fan_speed_gpu = current_fan_speed

            # Protect CPU Temperature
            # TO_BE_IMPLEMENTED

            # Regulate Fan Speed based on CPU Temperature
            new_fan_speed_cpu = self.run_temperature_controller(label = "CPU" , id = "cpu" , current_temp = cpu_temp , current_fan_speed = new_fan_speed_cpu)



            # Protect Drives Temperature
            self.run_temperature_protection(label = "DRIVE" , id = "drives/generic" , current_temp = drives_temps_max)

            # Regulate Fan Speed based on Drives Temperature
            new_fan_speed_drive = self.run_temperature_controller(label = "Drive" , id = "drives/generic" , current_temp = drives_temps_max , current_fan_speed = new_fan_speed_drive)



            # Protect HDD Temperature
            self.run_temperature_protection(label = "HDD" , id = "drives/hdd" , current_temp = hdd_temps_max)

            # Regulate Fan Speed based on HDD Temperature
            new_fan_speed_hdd = self.run_temperature_controller(label = "HDD" , id = "drives/hdd" , current_temp = hdd_temps_max , current_fan_speed = new_fan_speed_hdd)



            # Protect SSD Temperature
            self.run_temperature_protection(label = "SSD" , id = "drives/ssd" , current_temp = ssd_temps_max)

            # Regulate Fan Speed based on SSD Temperature
            new_fan_speed_ssd = self.run_temperature_controller(label = "SSD" , id = "drives/ssd" , current_temp = ssd_temps_max , current_fan_speed = new_fan_speed_ssd)



            # Protect NVME Temperature
            self.run_temperature_protection(label = "NVME" , id = "drives/nvme" , current_temp = nvme_temps_max)

            # Regulate Fan Speed based on NVME Temperature
            new_fan_speed_nvme = self.run_temperature_controller(label = "NVME" , id = "drives/nvme" , current_temp = nvme_temps_max , current_fan_speed = new_fan_speed_nvme)


            # Protect NIC Temperature
            # self.run_temperature_protection(label = "NIC" , id = "ssd" , current_temp = nic_temps_max)

            # Regulate Fan Speed based on NIC Temperature
            # new_fan_speed_nic = self.run_temperature_controller(label = "NIC" , id = "nic" , current_temp = nic_temps_max , current_fan_speed = new_fan_speed_nic)



            # Protect GPU Temperature
            # self.run_temperature_protection(label = "GPU" , id = "gpu" , current_temp = gpu_temps_max)

            # Regulate Fan Speed based on NIC Temperature
            # new_fan_speed_gpu = self.run_temperature_controller(label = "GPU" , id = "gpu" , current_temp = gpu_temps_max , current_fan_speed = new_fan_speed_gpu)


            # Get worst Case
            #new_fan_speed = max([new_fan_speed_cpu , new_fan_speed_drive])
            new_fan_speed = max(
                                [
                                    new_fan_speed_cpu,
                                    new_fan_speed_drive,
                                    new_fan_speed_hdd,
                                    new_fan_speed_ssd,
                                    new_fan_speed_nvme
                                ]
                                )

            # Set Fan Speed
            if new_fan_speed != current_fan_speed:
                # Echo
                log_info(f"Fan Controller: Updating Fan Speed from {current_fan_speed}% to {new_fan_speed}%.")

                # Update
                self.set_fan_speed(new_fan_speed)
            else:
                # Echo
                log_debug(f"Fan Controller: No Fan Speed Update required. Keeping Fan Speed to {current_fan_speed}% but sending Reference Again.")

                # Prevent e.g. (external) manual testing from "blocking" the Fan Speed to a Low Value in case Fan Speed is already at 100%
                self.set_fan_speed(new_fan_speed)

            # Get and Log IPMI System Event Log
            try:
                self.get_system_event_log()
            except Exception as e:
                log_error(f"Event Log: Error Parsing the IPMI Event Log.",
                          exc_info=True
                          )

            # Wait UPDATE_INTERVAL seconds before checking the temperature again
            #pprint.pprint(global_data.config)
            time.sleep(global_data.config["general"]["update_interval"])


    def ipmi_set_fan_mode_full(self) -> None:
        # Echo
        log_info("Setting Fan Control Mode to Full (Manual)")

        # IPMI tool command to set the fan control mode to manual (Full)
        fan_speed_full = global_data.config["ipmi"]["fan_modes"]["full"]["registers"]
        cmd = ["ipmitool" , "raw"] + fan_speed_full
        Command(command = cmd , return_result = False , check_return_code = True)
        time.sleep(2)

    def ipmi_set_fan_mode_optimal(self) -> None:
        # Echo
        log_info("Setting Fan Control Mode to Optimal")
        log_info("This is needed because in some cases the Fan Speed is stuck, if already starting in Full Mode")

        # IPMI tool command to set the fan control mode to Optimal
        fan_speed_optimal = global_data.config["ipmi"]["fan_modes"]["optimal"]["registers"]
        cmd = ["ipmitool" , "raw"] + fan_speed_optimal
        Command(command = cmd , return_result = False , check_return_code = True)
        time.sleep(2)

    def set_fan_mode(self) -> None:
        # If IPMI Control Mode is set, follow IPMI initialization Procedure
        if global_data.config.get("ipmi", {}).get("enabled", False):
            # Setting Fan Control Mode to Optimal
            # This is needed because in some cases the Fan Speed is stuck, if already starting in Full Mode
            self.ipmi_set_fan_mode_optimal()

            # Setting Fan Control Mode to Full (Manual)
            self.ipmi_set_fan_mode_full()

    def configure(self):
        # Allow Function to modify global_data.config Global Variable
        # global global_data.config

        # Get Configuration Folder
        SUPERMICRO_FAN_CONTROL_CONFIG_PATH = os.getenv("SUPERMICRO_FAN_CONTROL_CONFIG_PATH")

        if SUPERMICRO_FAN_CONTROL_CONFIG_PATH is None:
            SUPERMICRO_FAN_CONTROL_CONFIG_PATH = "/etc/supermicro-fan-control/"

        # Echo
        log_info(f"Using Configuration Folder {SUPERMICRO_FAN_CONTROL_CONFIG_PATH}")

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
        # self.read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/boards.d/default.yml")
        self.read_config(f"{SUPERMICRO_FAN_CONTROL_CONFIG_PATH}/boards.d/{motherboard}.yml")

        # Print Configuration
        # pprint.pprint(CONFIG)
        # print(json.dumps(CONFIG, indent=4, sort_keys=True))

        # Set Fan Mode
        self.set_fan_mode()

        # Set the Correct Environment Variables
        for name in global_data.config["general"]["environment"]:
            # Get Value
            value = str(global_data.config["general"]["environment"][name])

            # Echo
            log_info(f"Environment: Set Environment Parameter {name} to {value}")

            # Set the Variable
            os.environ[name] = value

        # Set Log Level
        globals.LOG_LEVEL = global_data.config.get("log", {}).get("general", {}).get("level")

        app_logger = logging.getLogger("app")

        app_logger_level_str = globals.LOG_LEVEL
        app_logger_level_obj = logging.getLevelName(globals.LOG_LEVEL.upper())

        # logging.basicConfig(
        #     level=getattr(logging, app_logger_level_obj, logging.CRITICAL),
        #     format="[%(levelname)s] %(message)s",
        #     stream=sys.stdout,  # Outputs to stdout like your original print
        #     force=True
        # )

        app_logger.setLevel(app_logger_level_obj)

        # Avoid Log Duplication
        app_logger.propagate = False

        # 3. Create a StreamHandler (matches: stream=sys.stdout)
        app_handler = logging.StreamHandler(sys.stdout)

        # 4. Define the visual layout (matches: format="[%(levelname)s] %(message)s")
        app_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        app_handler.setFormatter(app_formatter)

        # 5. Attach the formatter to the handler, and the handler to the logger
        app_handler.setFormatter(app_formatter)
        app_logger.addHandler(app_handler)

        # 6. Dynamically resolve your parametric string (matches your getattr logic)
        # (Assumes app_logger_level_obj is a string like "debug" or "info")
        level_upper = str(app_logger_level_obj).upper()
        resolved_level = getattr(logging, app_logger_level_str.upper(), logging.CRITICAL)

        # 7. Apply the level to both the logger and the handler
        app_logger.setLevel(resolved_level)
        app_handler.setLevel(resolved_level)

        log_debug(f"Set LOG_LEVEL to {app_logger_level_str}")

        #os.environ['LOG_LEVEL'] = LOG_LEVEL
        #print(f"SET CONFIGURED LOG_LEVEL = {LOG_LEVEL}")


@api.get("/config",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_config():
    return global_data.config


@api.get("/temperatures",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_temperatures():
    return global_data.temperature_readings


@api.get("/temperatures/cpu",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_temperatures_cpu():
    return global_data.temperature_readings.get("cpu")

@api.get("/temperatures/ram",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_temperatures_ram():
    return global_data.temperature_readings.get("ram")


@api.get("/temperatures/drives",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_temperatures_drives():
    return global_data.temperature_readings.get("drives", {})


@api.get("/temperatures/hdd",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_temperatures_hdd():
    return global_data.temperature_readings.get("drives", {}).get("hdd")


@api.get("/temperatures/ssd",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_temperatures_ssd():
    return global_data.temperature_readings.get("drives", {}).get("ssd")


@api.get("/temperatures/nvme",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_temperatures_nvme():
    return global_data.temperature_readings.get("drives", {}).get("nvme")

@api.get("/temperatures/gpu",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_temperatures_gpu():
    return global_data.temperature_readings.get("gpu")

@api.get("/fans",
         summary="Query Fans Speeds",
         description="Returns Information about Fans Speeds",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_fan_speeds():
    return global_data.fan_speed_readings


@api.get("/pwm",
         summary="Query PWM References",
         description="Returns Information about PWM Speed References",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_pwn_speed_references():
    return global_data.fan_speed_references

@api.get("/voltages",
summary="Query Vltages",
description="Returns Information about Voltages",
# This performs Data Validation - if Output is invalid, Program crashes
# response_model=SystemStatusResponse
)
def api_get_voltages():
    return global_data.voltages_readings


@api.get("/bmc/sensors",
summary="Query BMC Sensors",
description="Returns Information about BMC Sensors",
# This performs Data Validation - if Output is invalid, Program crashes
# response_model=SystemStatusResponse
)
def api_get_bmc_sensors():
    return global_data.bmc_sensors_readings

@api.get("/bmc/event-log",
         summary="Query System Event Log",
         description="Returns BMC System Event Log",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_bmc_event_log():
    return global_data.bmc_event_log


@api.get("/info",
         summary="Information about the Fan Controller",
         description="Returns Fan Controller Information",
         # This performs Data Validation - if Output is invalid, Program crashes
         # response_model=SystemStatusResponse
)
def api_get_info():
    # Get the current process using its Process ID (PID)
    current_process = psutil.Process(os.getpid())

    # Current Time
    current_timestamp = datetime.datetime.now().timestamp()
    current_time = datetime.datetime.fromtimestamp(current_timestamp)
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # Get the time when the process was started (epoch timestamp)
    start_timestamp = current_process.create_time()
    start_time = datetime.datetime.fromtimestamp(start_timestamp)
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    # Calculate elapsed run time in seconds
    run_time_seconds = time.time() - start_timestamp

    # Debug
    # print(f"Process run time: {run_time_seconds:.2f} seconds")

    # start_timestamp = psutil.Process(os.getpid()).create_time()
    elapsed_time_seconds = current_time - start_time

    elapsed_time_str = str(elapsed_time_seconds)

    # Debug
    # print(f"Process run time: {elapsed_time_seconds}")

    # Format Output as Dictionary
    data = {}
    process_info = {}

    process_info["current_time"] = current_time_str
    process_info["current_timestamp"] = current_timestamp

    process_info["start_time"] = start_time_str
    process_info["start_timestamp"] = start_timestamp

    process_info["running_time"] = elapsed_time_str
    process_info["running_seconds"] = elapsed_time_seconds

    data["process"] = process_info

    # Return Dictionary
    return data

def start_server():
    # Get Web Server Configuration
    HTTP_BIND_HOST = global_data.config.get("web_server", {}).get("bind_address", "127.0.0.1")
    HTTP_BIND_PORT = global_data.config.get("web_server", {}).get("bind_port", 8080)

    # Get the folder where app.py actually lives
    # APP_DIR = os.path.dirname(os.path.abspath(__file__))
    # log_info(f"Set APP_DIR to {APP_DIR} for uvicorn")

    # Setting reload to False is required, since we launch uvicorn from inside Python Application
    config = uvicorn.Config(app=api,
                            host=HTTP_BIND_HOST,
                            port=HTTP_BIND_PORT,
                            reload=False,
                            log_config=None
                            )

    # Create Uvicorn Server
    server = uvicorn.Server(config)

    # Run Uvicorn Server
    server.run()

def start_controller():
    # Initialize Global Controller
    global_controller = GlobalController()

    # Initialize
    global_controller.init()

    # Configure
    global_controller.configure()

    if global_data.config.get("web_server", {}).get("enabled", False):
        # Launch Uvicorn on a background thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
    else:
        log_info(f"Skip Startup of Web Server (API) since it is disabled in Configuration.")

    # Get Fan Controller Configuration
    fan_controller_config = global_data.config["fan_controller"]

    # Override the initial Setting for current_fan_speed in case fan_controller_config["min_speed"] is higher
    if "initial_speed" in fan_controller_config:
        # Use the "initial_speed" Parameter or the Default Initial Value of current_fan_speed (50%), whichever is higher
        current_fan_speed = max(default_initial_fan_speed , fan_controller_config["initial_speed"])
    else:
        # Use the "min_speed" Parameter or the Default Initial Value of current_fan_speed (50%), whichever is higher
        current_fan_speed = max(default_initial_fan_speed , fan_controller_config["min_speed"])

    # Set initial minimum fan speed
    log_info(f"Set Initial Fan Speed to {current_fan_speed}%")
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

    # Debug
    log_debug(f"Parsed CLI Arguments: operation={args.operation}")
    log_debug(f"Parsed CLI Arguments: {args}")

    if args.operation == "start":
        start_controller()
    elif args.operation == "stop":
        stop_controller()
