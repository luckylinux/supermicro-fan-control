# Subprocess Python Module
from subprocess import Popen , PIPE, run

# Custom Wrapper Class to run System Commands
class Command:
    # Class Properties
    stdout
    stderr
    retcode
    stdin
    command_array
    command_string

    # Class Constructor
    def __init__(self):
        self.stdout = None
        self.stderr = None
        self.retcode = None
        self.stdin = None
        self.command_array = None
        self.command_string = None