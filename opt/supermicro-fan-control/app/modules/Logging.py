# Core Libraries
import os
import sys
from enum import Enum

# Import Global Variables
import globals

#from modules.Globals import *
#import modules.Globals as Globals
#import globals.CONFIG as CONFIG
#import globals.LOG_LEVEL as LOG_LEVEL
#from globals.LOG_LEVEL import LOG_LEVEL

#print(globals.LOG_LEVEL.LOG_LEVEL)
#print(LOG_LEVEL)
#print(LOG_LEVEL.LOG_LEVEL)


# Define Log Levels
class LogLevel(Enum):
    CRITICAL = 1
    ERROR = 2
    WARNING = 2
    INFO = 3
    DEBUG = 4

    @staticmethod
    def get_value(name):
        if name in LogLevel.__members__:
           return LogLevel[name].value
        else:
           return None

    @staticmethod
    def get_name(value):
        if value in LogLevel:
           return LogLevel(value).name
        else:
           return None

# Initialize LOG_LEVEL
#LOG_LEVEL = "DEBUG"

# Log
def log(message , level="INFO" , indent=0):
    # Debug
    #print(f"level = {level} , LOG_LEVEL = {LOG_LEVEL}")

    # Get LOG_LEVEL String Representation
    log_level_setting_str = globals.LOG_LEVEL

    # Get LOG_LEVEL Integer Representation
    log_level_setting_int = LogLevel.get_value(globals.LOG_LEVEL)

    # Get Log Level in Integer
    if level in LogLevel.__members__:
        # Get Corresponding Integer Value
        log_value_int = LogLevel[level].value
    else:
        # Echo Invalid
        print(f"[INVALID] INVALID LOG LEVEL: {level}.")

        # Default to Debug instead
        log_value_int = LogLevel["DEBUG"].value

    # Debug
    #print(f"level = {level} , LOG_LEVEL = {log_level_setting_str}")
    #print(f"log_value_int = {log_value_int} , log_level_setting = {log_level_setting_int}")

    # If level >= LOG_LEVEL then print it
    if log_value_int <= log_level_setting_int:
        # Format Indent
        indentString = "\t" * max(indent + 1 , 1)

        # Echo
        print(f"[{level}] {indentString}{message}")

        # syslog.syslog(syslog.LOG_INFO, f"Hex Speed: {hex_speed}")

        # Flush in order for Journalctl to show the newly added Lines
        sys.stdout.flush()
