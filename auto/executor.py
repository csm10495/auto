'''
Home to the Executor part of Auto
'''
import datetime
import os
import parseshebang
import pathlib
import shutil
import subprocess
import sys
import tempenv
import time
import threading
import typing

from auto.config import AutoConfig

class Executor:
    '''
    An Executor is responsible for executing the given run_path.

    It will use various options from the AutoConfig to determine how it
    should perform the execution.
    '''
    def __init__(self, config: AutoConfig, run_path: pathlib.Path):
        '''
        Initializer. Takes in an AutoConfig and a run_path.
        The run_path is the 'thing' we intend to execute and is likely
        either an executable, script, or something similar.
        '''
        self.config = config
        self.run_path = run_path
        self.logger = config.get_component_logger('executor')

        if not self.run_path.is_file():
            which_path = shutil.which(str(self.run_path))
            if not which_path:
                raise FileNotFoundError(f'{self.run_path} does not exist (and is not in PATH)')
            else:
                self.run_path = pathlib.Path(which_path)

    def get_process_max_runtime(self) -> int:
        ''' Gets the max runtime in seconds for an execution '''
        # 31556952 is one year.
        return self.config.get_executor_config().max_process_runtime_seconds or 31556952

    def get_pathext(self) -> typing.List[str]:
        ''' Gets a list of extensions that 'we can run directly via the shell' '''
        pathext = os.environ['PATHEXT'].split(os.pathsep)
        for i in self.config.get_executor_config().get('extensions_to_remove_from_pathext', []):
            if i in pathext:
                pathext.remove(i)
        return pathext

    def _log_process_stdout(self, process: subprocess.Popen):
        ''' Should be run in a thread to continually read output and send it to a logger. '''
        for stdout_line in process.stdout:
            stdout_line = stdout_line.decode().rstrip('\n').rstrip('\r')
            if stdout_line:
                self.logger.info(f">> {stdout_line}")

    def run_subprocess_output_to_logger(self, cmd: typing.Union[str, list]):
        '''
        Runs the given command using subprocess, along with options in the AutoConfig.
        Output will be logged to the logger.
        '''
        self.logger.info(f"Executing: {cmd}...")

        max_runtime = self.get_process_max_runtime()
        self.logger.debug(f".. With a max runtime of: {max_runtime} seconds.")
        death_time = max_runtime + time.time()
        self.logger.debug(f".. Process death time is: {datetime.datetime.fromtimestamp(death_time)}")

        process = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        self.logger.debug(f"Process pid: {process.pid}")

        # start a temp thread to keep track read the command output and
        # write it to the logger
        log_thread = threading.Thread(target=self._log_process_stdout, args=(process,))
        log_thread.start()

        # While waiting for the process to end, check for death time.
        # If death time passes, kill the process
        while process.poll() is None:
            if time.time() > death_time:
                self.logger.info("Killing process as death time has elapsed.")
                process.kill()
                process.terminate()

            # yield a bit
            time.sleep(.001)

        # once we get here the process should no longer be running
        exit_code = process.wait()
        log_thread.join()

        self.logger.info(f".. Exit Code: {exit_code}")

    def execute(self):
        '''
        Executes this Executor.

        Will attempt to figure out the best way to do that then ultimately
        perform a subprocess execution and waiting for it to complete
        '''
        extension = self.run_path.suffix.lstrip('.')
        pathext = self.get_pathext()
        with tempenv.TemporaryEnvironment({'PATHEXT' : os.pathsep.join(pathext)}):
            if extension in pathext:
                # should be able to run directly from command line
                self.logger.debug("About to do a PATHEX-based execution")
                self.run_subprocess_output_to_logger(str(self.run_path))
            elif extension in ('py', 'pyc'):
                # Run a python script with the running python
                self.logger.debug("About to do a Python-based execution")
                self.run_subprocess_output_to_logger([sys.executable, str(self.run_path)])
            else:
                # Attempt to read/use the shebang line
                self.logger.debug("About to do a Shebang-based execution")
                with open(self.run_path, 'r') as file:
                    shebang = parseshebang.parse(file)
                self.run_subprocess_output_to_logger(shebang + [str(self.run_path)])

# todo... this module needs unit tests.