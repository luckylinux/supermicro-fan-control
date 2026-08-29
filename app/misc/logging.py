# Core Libraries
# import os
import sys
from enum import Enum
from typing import Any

# Use Python built-in logging library
import logging
logger = logging.getLogger("app")
# logging.basicConfig(
#     level=getattr(logging, LOG_LEVEL_SETTING.upper(), logging.CRITICAL),
#     format="[%(levelname)s] %(message)s",
#     stream=sys.stdout,  # Outputs to stdout like your original print
# )

# Import Global Variables
import globals

# from misc.Globals import *
# import misc.Globals as Globals
# import globals.CONFIG as CONFIG
# import globals.LOG_LEVEL as LOG_LEVEL
# from globals.LOG_LEVEL import LOG_LEVEL

# print(globals.LOG_LEVEL.LOG_LEVEL)
# print(LOG_LEVEL)
# print(LOG_LEVEL.LOG_LEVEL)


# Define Log Levels
class LogLevel(Enum):
    CRITICAL = 1
    ERROR = 2
    WARNING = 3
    INFO = 4
    DEBUG = 5

    @staticmethod
    def get_value(name: str) -> int:
        if name in LogLevel.__members__:
           return LogLevel[name].value
        else:
           # Default to Critical
           return 1

           # Return undefined
           # return None

    @staticmethod
    def get_name(value: int) -> str | None:
        if value in LogLevel:
           return LogLevel(value).name
        else:
           return None

# Initialize LOG_LEVEL
# LOG_LEVEL = "DEBUG"

# Log
def log_generic(message: str,
                *args: Any,
                level: str = "INFO",
                indent: int = 0,
                exc_info: bool | tuple | Exception | None = None,
                stack_info: bool = False,
                stacklevel: int = 1,
                extra: dict | None = None,
                ) -> None:

    # Debug
    # print(f"level = {level} , LOG_LEVEL = {LOG_LEVEL}")

    # Get LOG_LEVEL String Representation
    # log_level_setting_str = globals.LOG_LEVEL

    # Get LOG_LEVEL Integer Representation
    # log_level_setting_int = LogLevel.get_value(globals.LOG_LEVEL)

    # Get Log Level in Integer
    # if level in LogLevel.__members__:
    #     # Get Corresponding Integer Value
    #     log_value_int = LogLevel[level].value
    # else:
    #     # Echo Invalid
    #     logger.error(f"[INVALID] INVALID LOG LEVEL: {level}.")
    #
    #     # Default to Debug instead
    #     log_value_int = LogLevel["DEBUG"].value

    # Debug
    # print(f"level = {level} , LOG_LEVEL = {log_level_setting_str}")
    # print(f"log_value_int = {log_value_int} , log_level_setting = {log_level_setting_int}")

    # If level >= LOG_LEVEL then print it
    # if log_value_int <= log_level_setting_int:
    if True is True:
        # Format Indent
        indent_string = "\t" * max(indent + 1 , 1)
        formatted_message = f"{indent_string}{message}"

        # Map string levels to native logging methods
        level_upper = level.upper()

        if level_upper == "DEBUG":
            logger.debug(formatted_message,
                         exc_info=exc_info,
                         stack_info=stack_info,
                         stacklevel=stacklevel,
                         extra=extra
                         )

        elif level_upper == "INFO":
            logger.info(formatted_message,
                        exc_info=exc_info,
                        stack_info=stack_info,
                        stacklevel=stacklevel,
                        extra=extra

                        )

        elif level_upper == "WARNING":
            logger.warning(formatted_message,
                           exc_info=exc_info,
                           stack_info=stack_info,
                           stacklevel=stacklevel,
                           extra=extra

                           )

        elif level_upper == "ERROR":
            logger.error(formatted_message,
                         exc_info=exc_info,
                         stack_info=stack_info,
                         stacklevel=stacklevel,
                         extra=extra

                         )

        elif level_upper == "CRITICAL":
            logger.critical(formatted_message,
                            exc_info=exc_info,
                            stack_info=stack_info,
                            stacklevel=stacklevel,
                            extra=extra

                            )

        else:
            # Handle your [INVALID] fallback logic safely
            logger.error(f"\t[INVALID] INVALID LOG LEVEL: {level}.")
            logger.error(formatted_message)

        # syslog.syslog(syslog.LOG_INFO, f"Hex Speed: {hex_speed}")

        # Flush in order for Journalctl to show the newly added Lines
        sys.stdout.flush()

def log_debug(message: str,
              *args: Any,
              indent: int = 0,
              exc_info: bool | tuple | Exception | None = None,
              stack_info: bool = False,
              stacklevel: int = 1,
              extra: dict | None = None,
              ) -> None:

    log_generic(message,
                *args,
                level="DEBUG",
                indent=indent,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra
                )

def log_info(message: str,
             *args: Any,
             indent: int = 0,
             exc_info: bool | tuple | Exception | None = None,
             stack_info: bool = False,
             stacklevel: int = 1,
             extra: dict | None = None,
             ) -> None:

    log_generic(message,
                *args,
                level="INFO",
                indent=indent,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra
                )

def log_error(message: str,
              *args: Any,
              indent: int = 0,
              exc_info: bool | tuple | Exception | None = None,
              stack_info: bool = False,
              stacklevel: int = 1,
              extra: dict | None = None,
              ) -> None:

    log_generic(message,
                *args,
                level="ERROR",
                indent=indent,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra
                )

def log_warning(message: str,
                *args: Any,
                indent: int = 0,
                exc_info: bool | tuple | Exception | None = None,
                stack_info: bool = False,
                stacklevel: int = 1,
                extra: dict | None = None,
                ) -> None:

    log_generic(message,
                *args,
                level="WARNING",
                indent=indent,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra
                )

def log_critical(message: str,
                 *args: Any,
                 indent: int = 0,
                 exc_info: bool | tuple | Exception | None = None,
                 stack_info: bool = False,
                 stacklevel: int = 1,
                 extra: dict | None = None,
                 ) -> None:

    log_generic(message,
                *args,
                level="CRITICAL",
                indent=indent,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra
                )
