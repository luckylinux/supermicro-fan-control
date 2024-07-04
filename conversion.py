#!/usr/bin/python3

speed = 100
value = format(speed , "02x")
print(f"Speed: {speed} % -> Value: 0x{value} HEX")

maximum_speed_hex = 0x64
maximum_speed_dec = format(maximum_speed_hex * 100/255)
print(f"Maximum HEX Speed: {maximum_speed_hex} -> Maximum Value: {maximum_speed_dec}")
