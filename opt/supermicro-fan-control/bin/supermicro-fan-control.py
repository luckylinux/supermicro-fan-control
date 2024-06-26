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

# Set your desired temperature range and minimum fan speed
MIN_TEMP = 20                        # [°C]
MAX_TEMP = 25                        # [°C]
MIN_FAN_SPEED = 50                  # [%] Initial Fan Speed
current_fan_speed = MIN_FAN_SPEED    # [%] Current Fan Speed
UPDATE_INTERVAL = 5                  # [s] How often Temperatures shall be checked and Fan Speed updated accordingly

# IPMI tool command to set the fan control mode to manual (Full)
os.system("ipmitool raw 0x30 0x45 0x01 0x01")
time.sleep(2)


# Read Config File
def read_config(filepath = '/etc/supermicro-fan-control/settings.yaml'):
   # Declare List
   images = []

   with open(filepath, 'r') as f:
      # Open YAML File in Safe Mode
      #data = yaml.safe_load(f)
      data = list(yaml.load_all(f, Loader=SafeLoader))

      # Print
      print(data[0])

      # Length of list
      length = len(data)

      # Iterate over list
      for l in range(length):
         # Get Data of the current Iteration
         currentdata = data[l]

         # Iterate over currentdata
         for item in currentdata:
            print(item)

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

   # Return Result
   return images


# Try to read YAML Configuration
read_config("/etc/supermicro-fan-control/settings.yaml.default")
read_config("/etc/supermicro-fan-control/settings.yaml")

# Stop here for now
sys.exit(0)


# Get the current CPU temperature
def get_cpu_temperature():
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

    # Set the fan speed for all 4 zones
    os.system(f"ipmitool raw 0x30 0x70 0x66 0x01 0x00 0x{hex_speed}")
    time.sleep(2)
    os.system(f"ipmitool raw 0x30 0x70 0x66 0x01 0x01 0x{hex_speed}")
    time.sleep(2)

    # Log the fan speed change to syslog
    syslog.syslog(syslog.LOG_INFO, f"Fan speed adjusted to {speed}%")

    # Print the fan speed change to console
    print(f"Fan speed adjusted to {speed}% - {hex_speed}")

# Set initial minimum fan speed
set_fan_speed(MIN_FAN_SPEED)

# Infinite Loop
while True:
    # Get current CPU Temperature
    cpu_temp = get_cpu_temperature()

    # Print current CPU Temperature to Console
    print(f"Current CPU Temperature: {cpu_temp}°C")

    if cpu_temp > MAX_TEMP and current_fan_speed < 100:
        # Increase the fan speed by 10% to cool down the CPU
        new_fan_speed = min(current_fan_speed + 10, 100)
        set_fan_speed(new_fan_speed)
    elif cpu_temp < MIN_TEMP and current_fan_speed > MIN_FAN_SPEED:
        # Decrease the fan speed by 1% if the temperature is below the minimum threshold
        new_fan_speed = max(current_fan_speed - 1, MIN_FAN_SPEED)
        set_fan_speed(new_fan_speed)

    # Wait UPDATE_INTERVAL seconds before checking the temperature again
    time.sleep(UPDATE_INTERVAL)