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
