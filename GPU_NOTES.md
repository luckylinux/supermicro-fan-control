# GPU NOTES
## NVIDIA
### List available Output Field Codes:
```
nvidia-smi --help-query-gpu | grep -i fan
```

### Examples
```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits
36.18
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=power.draw
21.46
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=power.draw.average
50.69
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=power.draw
22.44
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=power.draw.instant
22.25
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=power.limit
170.00
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=power.min_limit
100.00
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=power.max_limit
187.00
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=module.power.draw.average
[N/A]
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --help-query-gpu | grep -i fan
"fan.speed"
The fan speed value is the percent of the product's maximum noise tolerance fan speed that the device's fan is currently intended to run at. This value may exceed 100% in certain cases. Note: The reported speed is the intended fan speed. If the fan is physically blocked and unable to spin, this output will not match the actual fan speed. Many parts do not report fan speeds because they rely on cooling via fans in the surrounding enclosure.
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=fan.speed
54
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=temperature.memory
N/A
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=temperature.gpu
47
```

```
root@MYHOST:/opt/supermicro-fan-control# nvidia-smi --format=csv,noheader,nounits --query-gpu=temperature.gpu.tlimit
[N/A]
```


## AMD
```
# Dump performance metrics cleanly as a JSON object
amd-smi metric --json
```

```
# Dump hardware specifications cleanly as a CSV file
amd-smi static --csv
```

Check Temperatures:
```
root@MYHOST:/opt/supermicro-fan-control# amd-smi metric --json | grep --color -A20 -B20 -i temp
```

```
root@MYHOST:/opt/supermicro-fan-control# amd-smi topology --json
[
    {
        "gpu": 0,
        "bdf": "0000:0b:00.0",
        "links": [
            {
                "gpu": 0,
                "bdf": "0000:0b:00.0",
                "weight": 0,
                "link_status": "ENABLED",
                "link_type": "SELF",
                "num_hops": 0,
                "bandwidth": "N/A"
            }
        ]
    }
]
```


Check Temperatures (Full Output Example):
```
root@MYHOST:/opt/supermicro-fan-control# amd-smi metric --json
[
    {
        "gpu": 0,
        "usage": {
            "gfx_activity": {
                "value": 1,
                "unit": "%"
            },
            "umc_activity": {
                "value": 0,
                "unit": "%"
            },
            "mm_activity": {
                "value": 0,
                "unit": "%"
            },
            "vcn_activity": [
                "N/A",
                "N/A",
                "N/A",
                "N/A"
            ],
            "jpeg_activity": [
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A"
            ]
        },
        "power": {
            "socket_power": {
                "value": 6,
                "unit": "W"
            },
            "gfx_voltage": {
                "value": "N/A",
                "unit": "mV"
            },
            "soc_voltage": {
                "value": "N/A",
                "unit": "mV"
            },
            "mem_voltage": {
                "value": "N/A",
                "unit": "mV"
            },
            "power_management": "ENABLED",
            "throttle_status": "UNTHROTTLED"
        },
        "clock": {
            "gfx_0": {
                "clk": {
                    "value": 800,
                    "unit": "MHz"
                },
                "min_clk": {
                    "value": 500,
                    "unit": "MHz"
                },
                "max_clk": {
                    "value": 2750,
                    "unit": "MHz"
                },
                "clk_locked": "N/A",
                "deep_sleep": "DISABLED"
            },
            "gfx_1": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "gfx_2": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "gfx_3": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "gfx_4": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "gfx_5": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "gfx_6": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "gfx_7": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "mem_0": {
                "clk": {
                    "value": 541,
                    "unit": "MHz"
                },
                "min_clk": {
                    "value": 96,
                    "unit": "MHz"
                },
                "max_clk": {
                    "value": 875,
                    "unit": "MHz"
                },
                "clk_locked": "N/A",
                "deep_sleep": "DISABLED"
            },
            "vclk_0": {
                "clk": {
                    "value": 666,
                    "unit": "MHz"
                },
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "DISABLED"
            },
            "vclk_1": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "vclk_2": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "vclk_3": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "dclk_0": {
                "clk": {
                    "value": 555,
                    "unit": "MHz"
                },
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "DISABLED"
            },
            "dclk_1": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "dclk_2": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            },
            "dclk_3": {
                "clk": "N/A",
                "min_clk": "N/A",
                "max_clk": "N/A",
                "clk_locked": "N/A",
                "deep_sleep": "N/A"
            }
        },
        "temperature": {
            "edge": {
                "value": 36,
                "unit": "C"
            },
            "hotspot": {
                "value": 37,
                "unit": "C"
            },
            "mem": {
                "value": 32,
                "unit": "C"
            }
        },
        "pcie": {
            "width": 8,
            "speed": {
                "value": 16,
                "unit": "GT/s"
            },
            "bandwidth": "N/A",
            "replay_count": "N/A",
            "l0_to_recovery_count": "N/A",
            "replay_roll_over_count": "N/A",
            "nak_sent_count": "N/A",
            "nak_received_count": "N/A",
            "current_bandwidth_sent": "N/A",
            "current_bandwidth_received": "N/A",
            "max_packet_size": "N/A"
        },
        "ecc": {
            "total_correctable_count": 0,
            "total_uncorrectable_count": 0,
            "total_deferred_count": 0,
            "cache_correctable_count": "N/A",
            "cache_uncorrectable_count": "N/A"
        },
        "ecc_blocks": "N/A",
        "fan": {
            "speed": 0,
            "max": 255,
            "rpm": 0,
            "usage": {
                "value": 0.0,
                "unit": "%"
            }
        },
        "voltage_curve": "N/A",
        "overdrive": "N/A",
        "perf_level": "AMDSMI_DEV_PERF_LEVEL_AUTO",
        "xgmi_err": "N/A",
        "energy": {
            "total_energy_consumption": {
                "value": 0.0,
                "unit": "J"
            }
        },
        "mem_usage": {
            "total_vram": {
                "value": 8176,
                "unit": "MB"
            },
            "used_vram": {
                "value": 202,
                "unit": "MB"
            },
            "free_vram": {
                "value": 7974,
                "unit": "MB"
            },
            "total_visible_vram": {
                "value": 8176,
                "unit": "MB"
            },
            "used_visible_vram": {
                "value": 202,
                "unit": "MB"
            },
            "free_visible_vram": {
                "value": 7974,
                "unit": "MB"
            },
            "total_gtt": {
                "value": 64357,
                "unit": "MB"
            },
            "used_gtt": {
                "value": 65,
                "unit": "MB"
            },
            "free_gtt": {
                "value": 64292,
                "unit": "MB"
            }
        }
    }
]
```

Check Temperature Thresholds:
```
root@MYHOST:/opt/supermicro-fan-control# amd-smi static --json | grep --color -A20 -B20 -i temp
```

Check all Thresholds:
```
root@pve028:~# amd-smi static --json
[
    {
        "gpu": 0,
        "asic": {
            "market_name": "Navi 23 [Radeon RX 6600/6600 XT",
            "vendor_id": "0x1002",
            "vendor_name": "Advanced Micro Devices Inc. [AMD/ATI]",
            "subvendor_id": "0x1043",
            "device_id": "0x73ff",
            "rev_id": "0xc7",
            "asic_serial": "N/A",
            "oam_id": "N/A"
        },
        "bus": {
            "bdf": "0000:0b:00.0",
            "max_pcie_width": 16,
            "max_pcie_speed": {
                "value": 16,
                "unit": "GT/s"
            },
            "pcie_interface_version": "Gen 4",
            "slot_type": "CEM"
        },
        "vbios": {
            "name": "73FFHB.20.3.0.30.AS05",
            "build_date": "2021/12/01 00:51",
            "part_number": "115-D534P00-100",
            "version": "020.003.000.030.000000"
        },
        "limit": {
            "max_power": {
                "value": 100,
                "unit": "W"
            },
            "min_power": {
                "value": 94,
                "unit": "W"
            },
            "socket_power": {
                "value": 100,
                "unit": "W"
            },
            "slowdown_edge_temperature": {
                "value": 100,
                "unit": "C"
            },
            "slowdown_hotspot_temperature": {
                "value": 110,
                "unit": "C"
            },
            "slowdown_vram_temperature": {
                "value": 100,
                "unit": "C"
            },
            "shutdown_edge_temperature": {
                "value": 105,
                "unit": "C"
            },
            "shutdown_hotspot_temperature": {
                "value": 115,
                "unit": "C"
            },
            "shutdown_vram_temperature": {
                "value": 105,
                "unit": "C"
            }
        },
        "driver": {
            "name": "amdgpu",
            "version": "7.0.0-3-pve"
        },
        "board": {
            "model_number": "N/A",
            "product_serial": "N/A",
            "fru_id": "N/A",
            "product_name": "N/A",
            "manufacturer_name": "N/A"
        },
        "ras": {
            "eeprom_version": "N/A",
            "parity_schema": "N/A",
            "single_bit_schema": "N/A",
            "double_bit_schema": "N/A",
            "poison_schema": "N/A",
            "ecc_block_state": "N/A"
        },
        "partition": {
            "compute_partition": "N/A",
            "memory_partition": "N/A"
        },
        "dpm_policy": "N/A",
        "xgmi_plpd": "N/A",
        "process_isolation": "Disabled",
        "numa": {
            "node": 0,
            "affinity": -1
        },
        "vram": {
            "type": "GDDR6",
            "vendor": "MICRON",
            "size": {
                "value": 8176,
                "unit": "MB"
            }
        },
        "cache_info": [
            {
                "cache": 0,
                "cache_properties": [
                    "DATA_CACHE",
                    "SIMD_CACHE"
                ],
                "cache_size": {
                    "value": 16,
                    "unit": "KB"
                },
                "cache_level": 1,
                "max_num_cu_shared": 8,
                "num_cache_instance": 46
            },
            {
                "cache": 1,
                "cache_properties": [
                    "INST_CACHE",
                    "SIMD_CACHE"
                ],
                "cache_size": {
                    "value": 32,
                    "unit": "KB"
                },
                "cache_level": 1,
                "max_num_cu_shared": 2,
                "num_cache_instance": 14
            },
            {
                "cache": 2,
                "cache_properties": [
                    "DATA_CACHE",
                    "SIMD_CACHE"
                ],
                "cache_size": {
                    "value": 2048,
                    "unit": "KB"
                },
                "cache_level": 2,
                "max_num_cu_shared": 26,
                "num_cache_instance": 1
            },
            {
                "cache": 3,
                "cache_properties": [
                    "DATA_CACHE",
                    "SIMD_CACHE"
                ],
                "cache_size": {
                    "value": 32768,
                    "unit": "KB"
                },
                "cache_level": 3,
                "max_num_cu_shared": 26,
                "num_cache_instance": 1
            }
        ]
    }
]
```

```
### root@MYHOST:/opt/supermicro-fan-control# rocm-smi --showallinfo --json 2> /dev/null | jq -r
{
  "card0": {
    "Device Name": "Navi 23 [Radeon RX 6600/6600 XT/6600M]",
    "Device ID": "0x73ff",
    "Device Rev": "0xc7",
    "Subsystem ID": "0x05d5",
    "GUID": "17901",
    "Unique ID": "N/A",
    "VBIOS version": "115-D534P00-100",
    "Performance Level": "unknown",
    "GPU use (%)": "0",
    "GPU Memory Allocated (VRAM%)": "1",
    "Memory Activity": "N/A",
    "GPU memory vendor": "micron",
    "Serial Number": "N/A",
    "PCI Bus": "0000:0B:00.0",
    "ASD firmware version": "0x21000110",
    "CE firmware version": "37",
    "ME firmware version": "64",
    "MEC firmware version": "134",
    "MEC2 firmware version": "134",
    "PFP firmware version": "109",
    "RLC firmware version": "86",
    "SDMA firmware version": "76",
    "SDMA2 firmware version": "76",
    "SMC firmware version": "00.59.50.00",
    "SOS firmware version": "0x00230b09",
    "VCN firmware version": "0x0412100f",
    "Card Series": "Navi 23 [Radeon RX 6600/6600 XT/6600M]",
    "Card Model": "0x73ff",
    "Card Vendor": "Advanced Micro Devices, Inc. [AMD/ATI]",
    "Card SKU": "D534P00",
    "Node ID": "1",
    "GFX Version": "gfx1032"
  },
  "system": {
    "Driver version": "7.0.0-3-pve"
  }
}
```




```
amdsmi.amdsmi_get_gpu_metrics_info(device)

{'average_dclk0_frequency': 555,
 'average_dclk1_frequency': 0,
 'average_gfx_activity': 0,
 'average_gfxclk_frequency': 11,
 'average_mm_activity': 0,
 'average_socclk_frequency': 'N/A',
 'average_socket_power': 4,
 'average_uclk_frequency': 2,
 'average_umc_activity': 0,
 'average_vclk0_frequency': 666,
 'average_vclk1_frequency': 0,
 'current_dclk0': 555,
 'current_dclk0s': [555, 'N/A', 'N/A', 'N/A'],
 'current_dclk1': 0,
 'current_fan_speed': 0,
 'current_gfxclk': 700,
 'current_gfxclks': [700, 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'],
 'current_socclk': 640,
 'current_socclks': [640, 'N/A', 'N/A', 'N/A'],
 'current_socket_power': 'N/A',
 'current_uclk': 96,
 'current_vclk0': 666,
 'current_vclk0s': [666, 'N/A', 'N/A', 'N/A'],
 'current_vclk1': 0,
 'energy_accumulator': 0,
 'firmware_timestamp': 18446744073709551606,
 'gfx_activity_acc': 'N/A',
 'gfxclk_lock_status': 'N/A',
 'indep_throttle_status': False,
 'jpeg_activity': ['N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A',
                   'N/A'],
 'mem_activity_acc': 'N/A',
 'pcie_bandwidth_acc': 'N/A',
 'pcie_bandwidth_inst': 'N/A',
 'pcie_l0_to_recov_count_acc': 'N/A',
 'pcie_link_speed': 160,
 'pcie_link_width': 8,
 'pcie_nak_rcvd_count_acc': 'N/A',
 'pcie_nak_sent_count_acc': 'N/A',
 'pcie_replay_count_acc': 'N/A',
 'pcie_replay_rover_count_acc': 'N/A',
 'system_clock_counter': 69152974890086,
 'temperature_edge': 37,
 'temperature_hbm': ['N/A', 'N/A', 'N/A', 'N/A'],
 'temperature_hotspot': 37,
 'temperature_mem': 32,
 'temperature_vrgfx': 40,
 'temperature_vrmem': 0,
 'temperature_vrsoc': 42,
 'throttle_status': False,
 'vcn_activity': ['N/A', 'N/A', 'N/A', 'N/A'],
 'voltage_gfx': 'N/A',
 'voltage_mem': 'N/A',
 'voltage_soc': 'N/A',
 'xgmi_link_speed': 'N/A',
 'xgmi_link_width': 'N/A',
 'xgmi_read_data_acc': ['N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'],
 'xgmi_write_data_acc': ['N/A',
                         'N/A',
                         'N/A',
                         'N/A',
                         'N/A',
                         'N/A',
                         'N/A',
                         'N/A']}

```
