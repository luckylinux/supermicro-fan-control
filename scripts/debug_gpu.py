#!/usr/bin/env python3

# Import Libraries
import json
import pprint
import os
import sys

import ctypes
from typing import NewType

# Dynamically add the parent directory to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

from gpu.amd import AMDGPU

# Create the distinct type helper
AmdSmiProcessorHandle = NewType('AmdSmiProcessorHandle', ctypes.c_void_p)

# Import amdsmi Library
from amdsmi_commands import AMDSMICommands
from amdsmi_parser import AMDSMIParser
from amdsmi_logger import AMDSMILogger
import amdsmi_cli_exceptions
import amdsmi
from amdsmi import amdsmi_interface
from amdsmi import amdsmi_exception

if __name__ == "__main__":
    # Initialize GPU
    amdgpu = AMDGPU()

    # Initialize the modern system management interface
    amdsmi.amdsmi_init()

    # Get Processors
    devices_handles = amdsmi.amdsmi_get_processor_handles()

    # Initialize List
    temperatures_list = []

    for index, device in enumerate(devices_handles):
        # Get all Metrics
        # metrics = amdsmi.amdsmi_get_gpu_metrics_info(device)
        # pprint.pprint(metrics)

        # Get Temperature
        edge_temp = amdsmi.amdsmi_get_temp_metric(device,
                                                  amdsmi.AmdSmiTemperatureType.EDGE,
                                                  amdsmi.AmdSmiTemperatureMetric.CURRENT
                                                  )

        hots_temp = amdsmi.amdsmi_get_temp_metric(device,
                                                  amdsmi.AmdSmiTemperatureType.HOTSPOT,
                                                  amdsmi.AmdSmiTemperatureMetric.CURRENT
                                                  )

        junc_temp = amdsmi.amdsmi_get_temp_metric(device,
                                                  amdsmi.AmdSmiTemperatureType.JUNCTION,
                                                  amdsmi.AmdSmiTemperatureMetric.CURRENT
                                                  )

        vram_temp = amdsmi.amdsmi_get_temp_metric(device,
                                                  amdsmi.AmdSmiTemperatureType.VRAM,
                                                  amdsmi.AmdSmiTemperatureMetric.CURRENT
                                                  )

        #plx_temp = amdsmi.amdsmi_get_temp_metric(device,
        #                                          amdsmi.AmdSmiTemperatureType.PLX,
        #                                          amdsmi.AmdSmiTemperatureMetric.CURRENT
        #                                          )
        # print(f"PLX = {plx_temp} degrees")

        #hbm0_temp = amdsmi.amdsmi_get_temp_metric(device,
        #                                          amdsmi.AmdSmiTemperatureType.HBM0,
        #                                          amdsmi.AmdSmiTemperatureMetric.CURRENT
        #                                          )
        #print(f"HBM0 = {hbm0_temp} degrees")

        #hbm1_temp = amdsmi.amdsmi_get_temp_metric(device,
        #                                          amdsmi.AmdSmiTemperatureType.HBM1,
        #                                          amdsmi.AmdSmiTemperatureMetric.CURRENT
        #                                          )
        #print(f"HBM1 = {hbm1_temp} degrees")

        #hbm2_temp = amdsmi.amdsmi_get_temp_metric(device,
        #                                          amdsmi.AmdSmiTemperatureType.HBM2,
        #                                          amdsmi.AmdSmiTemperatureMetric.CURRENT
        #                                          )
        #print(f"HBM2 = {hbm2_temp} degrees")

        #hmb3_temp = amdsmi.amdsmi_get_temp_metric(device,
        #                                          amdsmi.AmdSmiTemperatureType.HBM3,
        #                                          amdsmi.AmdSmiTemperatureMetric.CURRENT
        #                                          )
        #print(f"HBM3 = {hbm3_temp} degrees")

        # pprint.pprint(temperatures)
        print(f"\tEdge = {edge_temp} degrees, Hotspot = {hots_temp} degrees, Junction = {junc_temp} degrees, VRAM = {vram_temp} degrees")

        # Get Temperatures
        #device_temperature = get_temperature(device=device)

        # Append to List
        #temperatures_list.append(device_temperature)
