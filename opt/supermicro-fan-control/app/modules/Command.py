# Core Libraries
import os
import sys

# Subprocess Python Module
#from subprocess import Popen , PIPE, run
import subprocess

# Import Custom Libraries
from modules.Logging import log

# Custom Wrapper Class to run System Commands
class Command:
    # Command Inputs / Results
    stdout = None
    stderr = None
    stdin = None
    returncode = None

    # Subprocess POpen Object
    pobj = None

    # Command in Array Form
    command_array = None

    # Command in String Form (Overall)
    command_string_overall = None

    # Command in String Form (for each Pipe)
    command_string_pipes = None

    # Settings
    return_result = False
    check_return_code = True
    print_stdin = False
    print_stdout = False 
    print_stderr = True
    debug = False

    # Overall Exit Code
    exitcode = None


    # Class Constructor
    def __init__(self , command = None , return_result = False , check_return_code = True , print_stdin = False , print_stdout = False , print_stderr = True , debug = False):
        # Command Inputs / Results
        self.stdout = None
        self.stderr = None
        self.returncode = None
        self.stdin = None

        # Subprocess POpen Object
        self.pobj = None
        
        # Command in Array Form
        self.command_array = None

        # Command in String Form (Overall)
        self.command_string_overall = None

        # Command in String Form (for each Pipe)
        self.command_string_pipes = []

        # Internal Quantitiees
        self.number_pipes = 0

        # Settings
        self.return_result = return_result
        self.check_return_code = check_return_code
        self.print_stdin = print_stdin
        self.print_stdout = print_stdout
        self.print_stderr = print_stderr
        self.debug = debug

        # Overall Exit Code
        self.exitcode = 0

        # Run Directly the requested Command if it's set
        if command is not None:
            self.run(command = command)

    # Run Command
    def run(self , command):
        # Save Command Array
        if not isinstance(command[0] , list):
            # Encapsulate everything in an external List
            self.command_array = [command]
        else:
            # Just use as-is
            self.command_array = command

        # Echo Overall Command
        log(f"Running Command (Complete Array): {self.command_array}" , level="DEBUG")

        # Debugging
        #rows = len(new_command)
        #cols = len(new_command[0])
        #trows = type(new_command)
        #tcols = type(new_command[0])
        #print(f"Array Dimension: {rows} Rows x {cols} Columns")
        #print(f"Types: {trows} (Rows) - {tcols} (Cols)")

        # Count Number of Pipes
        self.number_pipes = len(self.command_array)

        # If self.check_return_code is already specified as an array keep it, otherwise convert to array of same size as self.number_pipes
        if isinstance(self.check_return_code , bool):
            self.check_return_code = [self.check_return_code] * self.number_pipes
        elif len(self.check_return_code) != self.number_pipes:
            self.check_return_code = [self.check_return_code[0]] * self.number_pipes
            
        # Size Arrays Appropriately
        self.stdout = [None] * self.number_pipes
        self.stderr = [None] * self.number_pipes
        self.stdin = [None] * self.number_pipes
        self.pobj = [None] * self.number_pipes
        self.returncode = [None] * self.number_pipes
        self.command_string_pipes = [None] * self.number_pipes
        
        # Build Command String overall
        self.command_string_overall = ""

        # Loop over each Pipe
        for p in range(0 , self.number_pipes , 1):
            # String of each Pipe Command
            self.command_string_pipes[p] = ' '.join([str(item) for item in self.command_array[p]])

            # Join into a single String Command
            if self.command_string_overall == "":
                self.command_string_overall = self.command_string_pipes[p]
            else:
                self.command_string_overall = " | ".join([self.command_string_overall , self.command_string_pipes[p]])

        # Echo
        log(f"Running Command (Complete String): {self.command_string_overall}" , level="DEBUG")

        # Loop over each Pipe
        for p in range(0 , self.number_pipes , 1):
            # Echo
            log(f"Processing Command for Pipe #{p} (Array): {self.command_string_pipes[p]}" , level="DEBUG" , indent=1)
            log(f"Processing Command for Pipe #{p} (String): {self.command_array[p]}" , level="DEBUG" , indent=1)

            # Save Input
            if p == 0:
                self.stdin[p] = None
            else:
                self.stdin[p] = self.stdout[p-1]

                # Print Inputs (if Enabled)
                if self.print_stdin or self.debug:
                    log(f"Input Data: {self.stdin[p].decode()}" , level="DEBUG" , indent=2)
                    #print(self.stdin[p].decode())

            # Use Pipe
            self.pobj[p] = subprocess.Popen(' '.join(self.command_array[p]) , shell=True , stdin=subprocess.PIPE , stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Fetch Result and Pass Input Data
            if p == 0:
                # No Input
                self.stdout[p] , self.stderr[p] = self.pobj[p].communicate()
            else:
                # Chain Previous Command's Output as Input
                self.stdout[p] , self.stderr[p] = self.pobj[p].communicate(input=self.stdout[p-1])

            # Save Return Code
            self.returncode[p] = self.pobj[p].wait()

            # Print Errors (if Enabled)
            if self.print_stderr or self.debug:
                # Only show Message if value is non-empty
                text_stderr = self.stderr[p].decode()
                if text_stderr is not None and len(text_stderr) > 0:
                    log(f"Error Data: {text_stderr}" , level="DEBUG" , indent=2)
                    #print(self.stderr[p].decode())

            # Print Output (if Enabled)
            if self.print_stdout or self.debug:
                log(f"Output Data: {self.stdout[p].decode()}" , level="DEBUG" , indent=2)
                #print(self.stdout[p].decode())

            # If Return Code Check if enabled for any of the Pipes
            if self.check_return_code[p]:
                # Check if any Return Code is non-Zero
                if self.returncode[p]:
                    # Get stdout and stderr
                    text_output = self.stdout[p].decode().rsplit("\n")
                    text_error = self.stderr[p].decode().rsplit("\n")

                    # Log Error and stderr Content
                    log(f"Command exited with a non-Zero Error Code" , level="ERROR")
                    log(f"{text_error}" , level="ERROR")

                    # Store this critical Failure in the Global Exitcode
                    self.exitcode = self.returncode[p]
                else:
                    # Get stdout
                    text_output = self.stdout[p].decode().rsplit("\n")

                    # ...
                    # (not implemented)

        
        # Get Final Result
        retcode = self.returncode[-1]

        # Return latest Result
        if self.return_result:
            return self.stdout[-1]

    # Get Result
    def getResult(self , decode=True):
        return self.getOutput(decode)

    # Get Output
    def getOutput(self , decode=True):
        if decode:
            return self.stdout[-1].decode()
        else:
            return self.stdout[-1]