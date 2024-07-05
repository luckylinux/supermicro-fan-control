# Core Libraries
import os
import sys

# Log
def log(message , level="INFO" , indent=0):
    # Format Indent
    indentString = "\t" * max(indent + 1 , 1)

    # Echo
    print(f"[{level}] {indentString}{message}")

    # syslog.syslog(syslog.LOG_INFO, f"Hex Speed: {hex_speed}")

    # Flush in order for Journalctl to show the newly added Lines
    sys.stdout.flush()