# Import Core Libraries
# import logging
# import sys
# import pprint
import json
import time
# from copy import deepcopy

import ctypes
from typing import NewType

from misc.logging import log_critical, log_error, log_warning, log_info, log_debug

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

# Class Definition
class AMDGPU:
    # Class Attributes
    devices_list: list[dict]
    devices_handles: list[AmdSmiProcessorHandle]

    # Class Constructor
    def __init__(self) -> None:
        # Echo
        print("Initilize AMDGPU Object. Initialize amdsmi Connection ...")

        # Initialize Class Attributes
        self.devices_list = []
        self.devices_handles = []

        try:
            # Debug
            print(f"Beging initializing AMDGPU Object")

            # Initialize the modern system management interface
            amdsmi.amdsmi_init()

            # Get Processors
            self.devices_handles = amdsmi.amdsmi_get_processor_handles()

            # Debug
            print(f"Found {len(self.devices_handles)} GPU Devices")

        except Exception as e:
            log_error("Error occurred while initializing amdgpu Object",
                      exc_info=True
                      )

        finally:
            # Init Devices
            self.init_devices()

            # Debug
            log_info("Finished initializing AMDGPU Object")

    # Class Destructor
    def __del__(self):
        # Echo
        print("Destroying AMDGPU Object. Shut down amdsmi Connection ...")

        # Always clean up library bindings safely
        amdsmi.amdsmi_shut_down()

    def get_static(self,
                   device: AmdSmiProcessorHandle
                   ) -> dict | None:

        static_data = {}

        try:
            # Get structural ASIC identifiers (market name, IDs)
            try:
                asic_info = amdsmi.amdsmi_get_gpu_asic_info(device)
                static_data["asic"] = asic_info
            except Exception as e:
                log_error(f"Error occurred: {e}",
                          exc_info=True
                          )

            # Get VBIOS version details
            try:
                vbios_info = amdsmi.amdsmi_get_gpu_vbios_info(device)
                static_data["vbios"] = vbios_info
            except Exception as e:
                log_error(f"Error occurred: {e}",
                          exc_info=True
                          )

            # Get hardwired VRAM allocation metrics
            try:
                vram_info = amdsmi.amdsmi_get_vram_info(device)
                static_data["vram"] = vram_info
            except Exception as e:
                log_error(f"Error occurred: {e}",
                          exc_info=True
                          )

            # Get physical PCIe hardware configurations
            try:
                pcie_info = amdsmi.amdsmi_get_pcie_info(device)
                static_data["pcie"] = pcie_info
            except Exception as e:
                log_error(f"Error occurred: {e}",
                          exc_info=True
                          )

        except Exception as e:
            log_error(f"Error fetching Static Data: {e}",
                      exc_info=True
                      )

        return static_data

    def get_asics(self) -> list[dict | None] | None:
        # Initialize List
        firmware_list = [self.get_asic(device=device) for device in self.devices_handles]

        # Return Value
        return firmware_list

    def get_asic(self,
                  device: AmdSmiProcessorHandle
                  ) -> dict | None:
        asic_info = amdsmi.amdsmi_get_gpu_asic_info(device)

        return {"gpu": self.get_header(device=device), "vbios": asic_info}

    def get_vbioses(self) -> list[dict | None] | None:
        # Initialize List
        vbios_list = [self.get_vbios(device=device) for device in self.devices_handles]

        # Return Value
        return vbios_list

    def get_vbios(self,
                  device: AmdSmiProcessorHandle
                  ) -> dict | None:
        vbios_info = amdsmi.amdsmi_get_gpu_vbios_info(device)

        return {"gpu": self.get_header(device=device), "vbios": vbios_info}

    def get_pcies(self) -> list[dict | None] | None:
        # Initialize List
        vbios_list = [self.get_pcie(device=device) for device in self.devices_handles]

        # Return Value
        return vbios_list

    def get_pcie(self,
                  device: AmdSmiProcessorHandle
                  ) -> dict | None:
        pcie_info = amdsmi.amdsmi_get_gpu_vbios_info(device)

        return {"gpu": self.get_header(device=device), "pcie": pcie_info}

    def get_metric(self,
                   device: AmdSmiProcessorHandle
                   ) -> dict:
        try:
            # Single bulk memory callout to query active clocks, power, and temps
            metrics_dict = amdsmi.amdsmi_get_gpu_metrics_info(device)
            return metrics_dict
        except Exception as e:
            log_error(f"Error fetching live Metrics: {e}",
                      exc_info=True
                      )
            return {}

    def get_monitor_payload(self,
                            device: AmdSmiProcessorHandle,
                            index: int = 0
                            ) -> dict | None:
        """Replicates a single polling frame of amd-smi monitor --json."""
        monitor_data = {"gpu": index}

        # Extract live dynamic metrics block
        try:
            metrics = amdsmi.amdsmi_get_gpu_metrics_info(device)
            monitor_data["metrics"] = {
                "power": metrics.get("current_socket_power"),
                "temperature_edge": metrics.get("temperature_edge"),
                "temperature_hotspot": metrics.get("temperature_hotspot"),
                "gfx_clock": metrics.get("current_gfxclk"),
                "mem_clock": metrics.get("current_uclk"),
                "gfx_activity": metrics.get("average_gfx_activity"),
                "mem_activity": metrics.get("average_umc_activity")
            }
        except Exception as e:
            log_error(f"Error fetching Monitor / Metrics: {e}",
                      exc_info=True
                      )
            monitor_data["metrics"] = "Unavailable"

        # Extract real-time fan telemetry
        try:
            # Index 0 targets the primary cooling fan assembly on the shroud
            fan_speed = amdsmi.amdsmi_get_gpu_fan_speed(device, 0)
            monitor_data["fan"] = {
                "speed_rpm": fan_speed
            }
        except Exception as e:
            log_error(f"Error fetching Monitor / Fan: {e}",
                      exc_info=True
                      )
            monitor_data["fan"] = "Unavailable"

        return monitor_data

    def get_topology_payload(devices: list[AmdSmiProcessorHandle]) -> dict | None:
        """Replicates amd-smi topology --json payload map."""
        topology_matrix = []

        for i, dev_src in enumerate(devices):
            gpu_entry = {
                "gpu": i,
                "link_accessibility": {},
                "weight": {},
                "hops": {},
                "link_type": {}
            }

            for j, dev_dst in enumerate(devices):
                target_key = f"gpu_{j}"

                if i == j:
                    # Introspect properties on itself
                    gpu_entry["link_accessibility"][target_key] = "ENABLED"
                    gpu_entry["weight"][target_key] = 0
                    gpu_entry["hops"][target_key] = 0
                    gpu_entry["link_type"][target_key] = "SELF"
                    continue

                # Query cross-device P2P capabilities (Requires Proxmox Kernel Access)
                try:
                    # amdsmi_topo_get_p2p_status checks hardware links and weights
                    p2p_status = amdsmi.amdsmi_topo_get_p2p_status(dev_src, dev_dst)

                    # Extract link parameters safely from the returned binding object
                    gpu_entry["link_accessibility"][target_key] = (
                        "ENABLED" if p2p_status.get("iommu_accessible") else "DISABLED"
                    )
                    gpu_entry["weight"][target_key] = p2p_status.get("weight", "N/A")
                    gpu_entry["hops"][target_key] = p2p_status.get("hops", "N/A")
                    gpu_entry["link_type"][target_key] = str(p2p_status.get("link_type", "UNKNOWN"))
                except Exception as e:
                    # Graceful fallback if driver path is restricted on host kernel
                    log_error(f"Error occurred while querying GPU Topology: {e}",
                              exc_info=True
                              )
                    gpu_entry["link_accessibility"][target_key] = "UNKNOWN"
                    gpu_entry["weight"][target_key] = "N/A"
                    gpu_entry["hops"][target_key] = "N/A"
                    gpu_entry["link_type"][target_key] = "N/A"

            topology_matrix.append(gpu_entry)

        return topology_matrix

    def get_firmware(self,
                     device: AmdSmiProcessorHandle,
                     index: int = 0
                     ) -> dict | None:

        """Replicates amd-smi firmware --json for a specific device handle."""
        gpu_fw_data = {
            "gpu": index,
            "firmware": []
        }

        try:
            # Query the hardware firmware allocation map
            fw_info = amdsmi.amdsmi_get_fw_info(device)

            # Depending on your exact ROCm/Driver variant package version,
            # fw_info can return a direct list or a dictionary wrapping a 'fw_list' key.
            fw_list = fw_info.get("fw_list", []) if isinstance(fw_info, dict) else fw_info

            for fw_block in fw_list:
                # Reconstruct the exact naming and versioning mapping matrix
                gpu_fw_data["firmware"].append({
                    "component": fw_block.get("fw_name"),    # e.g., 'SMU', 'PSP', 'VCN'
                    "version": fw_block.get("fw_version"),   # The integer representation
                    "id": fw_block.get("fw_id")             # Hardware microcontroller ID
                })

        except Exception as e:
            log_error(f"Error occurred while querying GPU Firmware: {e}",
                      exc_info=True
                      )

            # Fallback if specific hardware components restrict kernel read paths
            gpu_fw_data["firmware"] = f"Unavailable: {str(e)}"

        return gpu_fw_data

    def get_amd_smi_list(self) -> list[dict]:
        # Initialize the modern system management interface
        # amdsmi.amdsmi_init()

        gpu_list = []

        try:
            # Fetch the devices handle array
            devices = amdsmi.amdsmi_get_processor_handles()

            for index, device in enumerate(devices):
                # 1. Gather structural identifiers
                try:
                    bdf = amdsmi.amdsmi_get_gpu_device_bdf(device)
                    bdf_str = str(bdf)
                except Exception as e:
                    log_error(f"Error occurred while Querying GPU BDF: {e}",
                              exc_info=True
                              )
                    bdf_str = "Unknown"

                try:
                    uuid = amdsmi.amdsmi_get_gpu_device_uuid(device)
                except Exception as e:
                    log_error(f"Error occurred while querying GPU UUID: {e}",
                              exc_info=True
                              )
                    uuid = "Unknown"

                # 2. Gather board info details
                try:
                    board_info = amdsmi.amdsmi_get_gpu_board_info(device)
                    # pprint.pprint(board_info)
                    product_name = board_info.product_name
                    model_number = board_info.model_number
                except Exception as e:
                    log_error(f"Error occurred while querying board_info / product_name / model_number: {e}",
                              exc_info=True
                              )
                    product_name, model_number = "Unknown", "Unknown"

                # 3. Build the individual device dictionary
                gpu_data = {
                    "gpu": index,
                    "bdf": bdf_str,
                    "uuid": uuid,
                    "product_name": product_name,
                    "model_number": model_number
                }
                gpu_list.append(gpu_data)

        except Exception as e:
            log_error(f"Error occurred in get_amd_smi_list: {e}",
                      exc_info=True
                      )

        # finally:
        #     # Always clean up library bindings safely
        #     amdsmi.amdsmi_shut_down()

        # Serialize to JSON format matching the CLI tool behavior
        # return json.dumps({"devices": gpu_list}, indent=4)

        # Return dictionary
        return gpu_list

    def get_device_uuid(self,
                        device: AmdSmiProcessorHandle
                        ) -> str | None:

        try:
            uuid = amdsmi.amdsmi_get_gpu_device_uuid(device)
            # print(f"UUID: {uuid}")
        except amdsmi.AmdSmiException as e:
            log_error(f"Error occurred while retrieving GPU UUID: {e}",
                      exc_info=True
                      )

        return uuid

    def get_device_bdf(self,
                       device: AmdSmiProcessorHandle
                       ) -> str | None:
        try:
            bdf = amdsmi.amdsmi_get_gpu_device_bdf(device)
            bdf_str = str(bdf)
        except Exception as e:
            log_error(f"Error occurred while retrieving GPU BDF: {e}",
                      exc_info=True
                      )
            bdf_str = "Unknown"

        return bdf_str

    def get_device_pcie_addr(self,
                             device: AmdSmiProcessorHandle
                             ) -> str | None:

        return self.get_device_bdf(device=device)

    def init_devices(self) -> None:
        # Get Devices
        # devices = amdsmi.amdsmi_get_processor_handles()
        # devices = self.devices_handles

        # devices_dict = []
        # devices_handles = []

        for id, device in enumerate(self.devices_handles):
            # Extract PCIe Address
            bdf = self.get_device_bdf(device=device)

            # Extract the unique GPU UUID string
            uuid = self.get_device_uuid(device=device)

            # Extract the physical board metrics and serial details
            try:
                board_info = amdsmi.amdsmi_get_gpu_board_info(device)
                # board_info is a structural object containing hardware fields
                # pprint.pprint(board_info)
                # print(f"Model/Part Number: {board_info.model_number}")
                # print(f"Product Name: {board_info.product_name}")
                # print(f"Serial Number: {board_info.serial_number}")
            except amdsmi.AmdSmiException as e:
                log_error(f"Error occurred while trying to get board_info: {e}",
                          exc_info=True
                          )

            # Store Attributes inside dictionary
            device_dict = {}
            device_dict["id"] = id
            # device_dict["handle"] = device
            device_dict["uuid"] = uuid
            device_dict["bdf"] = bdf
            # device_dict["board_info"] = board_info

            # Add to List
            self.devices_list.append(device_dict)

            # Add to List
            # self.devices_handles.append(device)

            # Save Cache
            # self.devices_list = devices_list
            # self.devices_handles = deepcopy(devices_handles)

    def get_devices(self) -> list[dict]:
        return self.devices_list

    def get_header(self,
                   device: AmdSmiProcessorHandle
                   ) -> dict | None:

        for index, dev in enumerate(self.devices_handles):
            if device == dev:
                return self.devices_list[index]

    def get_temperatures(self) -> list[dict]:
        # Initialize List
        temperatures_list = []

        for index, device in enumerate(self.devices_handles):
            # Get Temperatures
            device_temperature = self.get_temperature(device=device)

            # Append to List
            temperatures_list.append(device_temperature)

        # Return Value
        return temperatures_list

    def get_temperature(self,
                        device: AmdSmiProcessorHandle
                        ) -> dict | None:
        #sensor_types = {
        #        "Edge (GPU)": amdsmi.AmdSmiTemperatureType.EDGE,
        #        "Junction (Hotspot)": amdsmi.AmdSmiTemperatureType.JUNCTION,
        #        "VRAM/Memory": amdsmi.AmdSmiTemperatureType.VRAM,
        #        "HBM 0": amdsmi.AmdSmiTemperatureType.HBM_0,
        #        "HBM 1": amdsmi.AmdSmiTemperatureType.HBM_1,
        #        "HBM 2": amdsmi.AmdSmiTemperatureType.HBM_2,
        #        "HBM 3": amdsmi.AmdSmiTemperatureType.HBM_3,
        #    }

        #for name, sensor_enum in sensor_types.items():
        #    try:
        #        # Query the current physical metric
        #        current_temp = amdsmi.amdsmi_get_temp_metric(
        #            device,
        #            sensor_enum,
        #            amdsmi.AmdSmiTemperatureMetric.CURRENT
        #        )
        #
        #        # Query the pre-configured hardware ceiling threshold
        #        crit_limit = amdsmi.amdsmi_get_temp_metric(
        #            device,
        #            sensor_enum,
        #            amdsmi.AmdSmiTemperatureMetric.CRITICAL
        #        )
        #
        #        print(f"{name:<20} : {current_temp}°C (Critical Limit: {crit_limit}°C)")
        #
        #    except amdsmi.AmdSmiException as e:
        #        # Some sensors are architecture-dependent (e.g., HBM vs GDDR VRAM)
        #        # This safely ignores unpopulated sensors on your target model
        #        continue

        metrics = amdsmi.amdsmi_get_gpu_metrics_info(device)

        # Debug all Metrics
        # pprint.pprint(metrics)

        # Get Values
        temp_edge = metrics.get("temperature_edge")
        temp_hotspot = metrics.get("temperature_hotspot")
        temp_mem = metrics.get("temperature_mem")
        temp_vrgfx = metrics.get("temperature_vrgfx")
        temp_vrmem = metrics.get("temperature_vrmem")
        temp_vrsoc = metrics.get("temperature_vrsoc")

        temps = []
        temps.append(temp_edge)
        temps.append(temp_hotspot)
        temps.append(temp_mem)
        temps.append(temp_vrgfx)
        if temp_vrmem > 0:
            temps.append(temp_vrmem)
        temps.append(temp_vrsoc)

        if isinstance(temps, list):
            temp_avg = sum(temps) / len(temps)
            temp_min = min(temps)
            temp_max = max(temps)

        # Define Temperature Dictionary
        temperatures_dict = {
                    "avg": temp_avg,
                    "min": temp_min,
                    "max": temp_max,
                    "details": {
                        "edge": {
                            "value": temp_edge,
                            "unit": "C"
                        },
                        "hotspot": {
                            "value": temp_hotspot,
                            "unit": "C"
                        },
                        "mem": {
                            "value": temp_mem,
                            "unit": "C"
                        },
                        "vrgfx": {
                            "value": temp_vrgfx,
                            "unit": "C"
                        },
                        "vrmem": {
                            "value": temp_vrmem,
                            "unit": "C"
                        },
                        "vrsoc": {
                            "value": temp_vrsoc,
                            "unit": "C"
                        },
                    }
                }

        return {"gpu": self.get_header(device=device), "temperatures": temperatures_dict}

    def get_vrams(self) -> list[dict | None] | None:
        # Initialize List
        vram_list = [self.get_vram(device=device) for device in self.devices_handles]

        # Return Value
        return vram_list

    def get_vram(self,
                  device: AmdSmiProcessorHandle
                  ) -> dict | None:

        vram_usage = amdsmi.amdsmi_get_gpu_vram_usage(device)

        vram_used = vram_usage['vram_used']
        vram_total = vram_usage['vram_total']
        vram_free = (vram_total - vram_used)

        # Define Temperature Dictionary
        vram_dict = {
                    "absolute": {
                        "free": {
                            "value": vram_free,
                            "unit": "MB"
                        },
                        "used": {
                            "value": vram_used,
                            "unit": "MB"
                        },
                        "total": {
                            "value": vram_total,
                            "unit": "MB"
                        },
                    },
                    "relative": {
                        "free": {
                            "value": round(vram_free/vram_total*100.0, 1),
                            "unit": "%"
                        },
                        "used": {
                            "value": round(vram_used/vram_total*100.0, 1),
                            "unit": "%"
                        },
                        "total": {
                            "value": round(100.0, 1),
                            "unit": "%"
                        },
                    }
                }

        return {"gpu": self.get_header(device=device), "vram": vram_dict}

    def get_powers(self) -> list[dict] | None:
        # Initialize List
        powers_list = []

        for index, device in enumerate(self.devices_handles):
            # Get Powers
            device_power = self.get_power(device=device)

            # Append to List
            powers_list.append(device_power)

        # Return Value
        return powers_list

    def get_power(self,
                  device: AmdSmiProcessorHandle
                  ) -> dict | None:

        powers = amdsmi.amdsmi_get_power_info(device)

        # Debug
        power_average = powers['average_socket_power']
        gfx_voltage = powers['gfx_voltage']
        power_limit = powers['power_limit']

        # Define Temperature Dictionary
        powers_dict = {

                    "details": {
                        "average_socket_power": {
                            "value": power_average,
                            "unit": "W"
                        },
                        "gfx_voltage": {
                            "value": gfx_voltage,
                            "unit": "V"
                        },
                        "power_limit": {
                            "value": power_limit,
                            "unit": "W"
                        },
                    }
                }

        return {"gpu": self.get_header(device=device), "powers": powers_dict}

    def get_device_board_info(self,
                          device: AmdSmiProcessorHandle
                          ) -> dict | None:

        try:
            board_info = amdsmi.amdsmi_get_gpu_board_info(device)
            # board_info is a structural object containing hardware fields
            # pprint.pprint(board_info)
            # print(f"Model/Part Number: {board_info.model_number}")
            # print(f"Product Name: {board_info.product_name}")
            # print(f"Serial Number: {board_info.serial_number}")
        except amdsmi.AmdSmiException as e:
            log_error(f"Error occurred while trying to retrieve board_info: {e}",
                      exc_info=True
                      )

        return board_info

# Main (Execution as a Script)
if __name__ == "__main__":
    # Hook into system bindings
    # amdsmi.amdsmi_init()

    try:
        # tic: Start the timer
        tic = time.perf_counter()

        # Initialize Class
        amdgpu = AMDGPU()

        # Devices
        devices = amdgpu.get_devices()
        print("Devices List:")
        print(json.dumps(devices, indent=2))

        # Temperatures
        temperatures = amdgpu.get_temperatures()
        print("Devices Temperatures:")
        print(json.dumps(temperatures, indent=2))

        # Powers
        powers = amdgpu.get_powers()
        print("Devices Powers:")
        print(json.dumps(powers, indent=2))

        # VRAM
        vrams = amdgpu.get_vrams()
        print("Devices VRAMs:")
        print(json.dumps(vrams, indent=2))

        # Manual Processing
        # output_payload = {"gpus": []}

        # for id, device in enumerate(devices):
        #     # Extract the unique GPU UUID string
        #     uuid = amdgpu.get_device_uuid(device=device)
        #
        #     # Extract the physical board metrics and serial details
        #     board_info = amdgpu.get_device_board_info(device=device)
        #
        #     fw_payload = amdgpu.get_firmware(device)
        #     output_payload["gpus"].append(fw_payload)

        # Emit standard structured JSON representation
        # print(json.dumps(output_payload, indent=2))

        # List GPUs
        # print(json.dumps(amdgpu.get_amd_smi_list(), indent=2))

        # pprint.pprint(get_static)
        # pprint.pprint(get_metric)

        # toc: Stop the timer and calculate elapsed time
        toc = time.perf_counter()
        print(f"Elapsed time: {toc - tic:.6f} seconds")

    except Exception as e:
        log_error(f"Error occurred: {e}",
                  exc_info=True
                  )

    finally:
        # Free context references
        amdsmi.amdsmi_shut_down()
