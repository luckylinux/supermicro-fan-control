#!/opt/supermicro-fan-control/venv/bin/python3
import os
import subprocess
import time
import syslog
import re

# Set your desired temperature range and minimum fan speed
MIN_TEMP = 40
MAX_TEMP = 50
MIN_FAN_SPEED = 5  # Sets an initial fan speed of 5% 
current_fan_speed = MIN_FAN_SPEED

# IPMI tool command to set the fan control mode to manual (Full)
os.system("ipmitool raw 0x30 0x45 0x01 0x01")
time.sleep(2)

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

while True:


    cpu_temp = get_cpu_temperature()

    # Print the current CPU temperature to console
    print(f"Current CPU temperature: {cpu_temp}°C")

    if cpu_temp > MAX_TEMP and current_fan_speed < 100:
        # Increase the fan speed by 10% to cool down the CPU
        new_fan_speed = min(current_fan_speed + 10, 100)
        set_fan_speed(new_fan_speed)
    elif cpu_temp < MIN_TEMP and current_fan_speed > MIN_FAN_SPEED:
        # Decrease the fan speed by 1% if the temperature is below the minimum threshold
        new_fan_speed = max(current_fan_speed - 1, MIN_FAN_SPEED)
        set_fan_speed(new_fan_speed)

    # Wait for 60 seconds before checking the temperature again
    time.sleep(60)