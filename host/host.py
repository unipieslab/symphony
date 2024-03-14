import sys # for exit
import orjson
import subprocess
import os
import statistics
import traceback
import rpyc
from time import sleep
import json
import re
from datetime import datetime
import logging
from time import time
import timeit
import math
from datetime import timedelta
import os 
import requests
from enum import Enum

#from GPIOClient import GPIOClient


os.environ["PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT"] = "20.0" 

class Tester_Shell_Constants(Enum):
    """
        PMD_THRESHOLD: This value determines the maximum acceptable power consumption for the PMD.
        SOC_THRESHOLD: This value determines the maximum acceptable power consumption for the SoC.
        TEMP_PMD_THRESHOLD: This value determines the maximum acceptable temperature of the experiment system.
        CURRENT_PMD_THRESHOLD_SCALE: This value determines the factor by which to increase the power consumption threshold of PMD.
        CURRENT_SOC_THRESHOLD_SCALE: This value determines the factor by which to increase the power consumption threshold for the System-on-Chip (SoC).
        TEMP_PMD_THRESHOLD_SCALE: This value determines the factor for increasing the temperature threshold.
        TIMEOUT_SCALE_BOOT: This value determines the factor by which to increase the boot time threshold.
        RESET_AFTER_CONCECUTIVE_ERRORS: This value determines the number of consecutive errors that must occur before the experiment system automatically resets.
        EFFECTIVE_SEC_PER_BATCH: This value determines the allocated time (in seconds) for each batch of benchmarks to run.
        BENCHMARK_VERIFICATOIN_REGEX: This value specifies the regular expression used to validate the output of a benchmark run. A successful match indicates the benchmark completed correctly.
    """
    PMD_THRESHOLD                      = 95.0
    SOC_THRESHOLD                      = 95.0
    TEMP_PMD_THRESHOLD                 = 90.0
    CURRENT_PMD_THRESHOLD_SCALE        = 1.02
    CURRENT_SOC_THRESHOLD_SCALE        = 1.02
    TEMP_PMD_THRESHOLD_SCALE           = 1.10
    TIMEOUT_SCALE_BOOT                 = 1.00
    TIMEOUT_COLD_CACHE_SCALE_BENCHMARK = 4.00
    RESET_AFTER_CONCECUTIVE_ERRORS     = 2.00
    EFFECTIVE_SEC_PER_BATCH            = 20.0
    BENCHMARK_VERIFICATOIN_REGEX       = r'Verification( +)=(. +.*)'

class Tester_Shell_Defaults(Enum):
    FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES = 100
    FINISH_AFTER_TOTAL_ERRORS            = 100

class Tester_Shell:
    class CustomFormatter(logging.Formatter):
        import logging
        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format = "%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s"
        #format = "%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s:%(lineno)d)"

        FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: grey + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = self.logging.Formatter(log_fmt)
            return formatter.format(record)

    def __init__(self):
        self.__initialize_logger()

        # Counters
        self.__power_cycle_counter: int = 0
        self.__reset_counter: int = 0
        self.__run_counter: int = 0
        self.__sdc_counter: int = 0 
        self.__total_errors: int = 0

        # Important dictionaries
        self.__voltage_commands: dict = {}
        self.__benchmark_commands: dict = {} 
        self.__timeouts: dict = {}
        self.__system_errors_per_benchmark: dict = {} 
        self.__network_errors_per_benchmark: dict = {}
        self.__batch_per_benchmark: dict = {}

        # Important lists
        self.__voltage_list: list = []
        self.__benchmark_list: list = []

        # Target related
        self.__target_ip: str = ""
        self.__target_port: str = ""
        
        self.__first_boot: bool = True
        self.__dmesg_index: int = 0
        self.__dmesg_diff: str = ""

        # Thresholds
        self.__current_pmd_threshold_max: float = 0
        self.__current_soc_threshold_max: float = 0
        self.__temp_pmd_threshold_max: float = 0

        # Run related
        self.__current_benchmark_id: str = ""
        self.__current_voltage_id: str = ""
        self.__current_benchmark_command: str = ""
        self.__current_voltage_command: str = ""

        self.__finish_after_total_effective_minutes: float = Tester_Shell_Defaults.FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES
        self.__finish_after_total_errors: float = Tester_Shell_Defaults.FINISH_AFTER_TOTAL_ERRORS

        self.__effective_total_elapsed_minutes: float = 0
        self.__experiment_total_elapsed_sec: float = 0.1

        self.__experiment_start_time: time = time()

        # Scales
        self.__timeout_scale_benchmark: float = 0

        # Debug flags.
        self.__disable_resets: bool  = False
        self.__save_thresholds: bool = True

    """
        <--- Private methods --->
    """
    def __initialize_logger(self):
        self.now = datetime.now() # current date and time
        self.log_date = self.now.strftime("%m_%d_%Y__%H_%M_%S")
        self.log_file_name = 'logs/log_' + self.log_date + '.log'
        # self.logging.INFO
        logging.basicConfig(filename=self.log_file_name, encoding='utf-8', format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s' \
            ,level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
        # formatter = self.logging.Formatter(fmt='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
        #                       datefmt='%Y-%m-%d,%H:%M:%S')

        screen_handler = logging.StreamHandler()
        screen_handler.setFormatter(self.CustomFormatter())
        logging.getLogger().addHandler(screen_handler)    

    def __update(self):
        self.__timeout_scale_benchmark = 2 * self.batch_per_benchmark[self.__current_benchmark_id] 

        self.__current_benchmark_command = self.benchmark_commands[self.__current_benchmark_id]
        self.__current_voltage_command = self.voltage_commands[self.__current_voltage_id]

    """
        <--- Methods for every implementation --->
    """
    def _load_experiment_attr_from_dict(self, src: dict):
        try:
            self.__voltage_commands   = src["voltage_commands"] 
            self.__benchmark_commands = src["benchmark_commands"] 
            self.__timeouts           = src["timeouts"] 
            self.__voltage_list       = src["voltage_list"]
            self.__benchmark_list     = src["benchmark_list"] 
            self.__target_ip          = src["target_ip"]
            self.__target_port        = src["target_port"]
        except KeyError as e:
            raise Exception("Missing value for: " + str(e.args[0]))

        # Set initial benchmark and voltage ids.
        self.__current_benchmark_id = self.__benchmark_list[0]
        self.__current_voltage_id   = self.__voltage_list[0]

        # Calculate the number of runs per batch for each benchmark.
        # And initialize the system/network errors per benchmark
        for benchmark in self.__benchmark_list:
            self.__batch_per_benchmark[benchmark] = Tester_Shell_Constants.EFFECTIVE_SEC_PER_BATCH/self.__timeouts[benchmark]
            self.__system_errors_per_benchmark[benchmark]  = 0
            self.__network_errors_per_benchmark[benchmark] = 0

        # Update the attributes of the Tester.
        self.__update()

    def _load_experiment_attr_from_json_file(self, src: str):
        with open(src) as json_file:
            json_content: dict = json.load(json_file)
            self._load_experiment_attr_by_dict(json_content)

    """
        <--- Implementation dependent methods --->
    """
    def _ovrd_detect_cache_upsets(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass

    def _ovrd_target_reset(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass

    def _ovrd_target_power_cycle(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass

def main():
    test = Tester_Shell()


if __name__ == '__main__':
    main()