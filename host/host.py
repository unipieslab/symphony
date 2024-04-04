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
    TIMEOUT_SCALE_VOLTAGE              = 1.20
    TIMEOUT_COLD_CACHE_SCALE_BENCHMARK = 4.00
    RESET_AFTER_CONCECUTIVE_ERRORS     = 2.00
    EFFECTIVE_SEC_PER_BATCH            = 20.0
    BENCHMARK_VERIFICATOIN_REGEX       = r'Verification( +)=(. +.*)'
    DMESG_TIMEOUT                      = 10.0
    NETWORK_TIMEOUT_SEC                = 2.00
    CMD_EXECUTION_ATTEMPT              = 1.00

class Tester_Shell_Defaults(Enum):
    FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES = 100
    FINISH_AFTER_TOTAL_ERRORS            = 100
    
class Tester_Shell_Power_Action(Enum):
    TARGET_POWER_BTN_PRESS = 0
    TARGET_RESET_BTN_PRESS = 1

class Tester_Batch:
    def __init__(self):
        self.__batch: dict = {}
        self.__run: int = 0

    def append_run_results(self, results: dict, correct: bool, dmesg_index: int, run_counter: int):
        """
            Save a result inside a batch.
        """
        results["correct"]     = correct
        results["dmesg_index"] = str(dmesg_index)
        results["run_counter"] = run_counter, 

        self.__batch[str(self.__run)] = results
        self.__run += 1

    def get_batch(self):
        return self.__batch

class Tester_DB:
    
    def __init__(self):
        pass

    def save_result_to_db(self):
        pass

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
        self.__temp_pmd_threshold_max: float = 0

        # Variables for maximum values.
        self.__current_pmd_max: float = 0
        self.__current_soc_max: float = 0

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
        self.__debug_disable_resets: bool  = False
        self.__debug_save_thresholds: bool = True

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
        self.__current_benchmark_id = 
        self.__timeout_scale_benchmark = 2 * self.batch_per_benchmark[self.__current_benchmark_id] 
        self.__current_benchmark_command = self.benchmark_commands[self.__current_benchmark_id]
        self.__current_voltage_command = self.voltage_commands[self.__current_voltage_id]
        self.__boot_timeout_sec = round(self.__timeouts["BOOT"] * Tester_Shell_Constants.TIMEOUT_SCALE_BOOT)
        self.__voltage_config_timeout = round(self.__timeouts[self.__current_voltage_id] * Tester_Shell_Constants.TIMEOUT_SCALE_VOLTAGE)
        self.__benchmark_timeout = 2 * round(self.__batch_per_benchmark[self.__current_benchmark_id] * self.__timeouts[self.__current_benchmark_id])
        self.__benchmark_cold_cache_timeout = round(self.__timeouts[self.__current_benchmark_id] * Tester_Shell_Constants.TIMEOUT_COLD_CACHE_SCALE_BENCHMARK)

        self.__target_set_voltage()
        self.__target_set_frequency()

    def __target_set_voltage(self):
        # TOOD - Remote execute the command to set the voltage.
        pass

    def __target_set_frequency(self):
        pass

    def __generate_result_name(self):
        now = self.datetime.now() # current date and time
        result_date = now.strftime("%m_%d_%Y__%H_%M_%S")
        result_file_name = 'results/' + self.__current_benchmark_id + "_" + self.__current_voltage_id + "_" + result_date + ".json"

        return result_file_name

    def __target_connect_common(self, excp_timeout_s: int, net_timeout_s: int, ):
        sleep_sec_excep = 0.5 
        conn_count_thresh =  int(excp_timeout_s / sleep_sec_excep)
        attemp_counter = 0
        first_error = True

        while True:
            try:
                c = rpyc.connect(self.__target_ip, self.__target_port)
                c._config['sync_request_timeout'] = excp_timeout_s

                if not c.closed:
                    return c
            
                return None
            except:
                if first_error == True:
                    self._ovrd_clacify_detected_error()
                first_error = False
                conn_count_thresh -= 1 
                attemp_counter += 1
                self.logging.warning('Remote is down..trying to connect. Attempt: ' + str(attemp_counter))
                sleep(sleep_sec_excep)
                if conn_count_thresh <= 0:
                    self._ovrd_unused_target_reset_button()
                    first_error = True
                    conn_count_thresh = int(net_timeout_s / sleep_sec_excep)

    """
        <--- Methods for every implementation --->
    """

    def _target_set_next_voltage(self):
        """
        """
        curr_vid_index = self.__voltage_list.index(self.__current_voltage_id)
        next_vid_index = curr_vid_index + 1
        if next_vid_index > len(self.__voltage_list):
            return False

        self.__current_voltage_id = self.__voltage_list[next_vid_index]
        self.__target_set_voltage()

        return True

    def _target_set_next_benchmark(self):
        """
        """
        curr_bid_index = self.__benchmark_list.index(self.__current_benchmark_id)
        next_bid_index = curr_bid_index + 1
        if next_bid_index > len(self.__benchmark_list):
            return False

        self.__current_benchmark_id = self.__benchmark_list[next_bid_index]
        self.__update()

        return True

    def _target_set_next_frequency(self):
        pass

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

    def _save_results(self, batch: Tester_Batch):
        result_name = self.__generate_result_name()
        while True:
            try:
                with open(result_name, "r"):
                    # Re generate the file name
                    result_name = self.__generate_result_name()
                    continue
            except FileNotFoundError:
                with open(result_name, "w") as result_file_json:
                    # Save the bach on the file.
                    json.dump(batch.get_batch(), result_file_json)
                break

    def _save_state(self):
        pass

    def _restore_state(self):
        pass

    def _power_handler(self, action: Tester_Shell_Power_Action):
        if self.__debug_disable_resets == True:
            return

        if action == Tester_Shell_Power_Action.TARGET_POWER_BTN_PRESS:
            self._ovrd_unused_target_power_button()
        elif action == Tester_Shell_Power_Action.TARGET_RESET_BTN_PRESS:
            self._ovrd_unused_target_reset_button()
            alive = self._remote_alive(self.__boot_timeout_sec, Tester_Shell_Constants.NETWORK_TIMEOUT_SEC)
            while not alive:
                # TODO - is this right? rethink it. What if the computer never turn on again.
                alive = self._remote_alive(self.__boot_timeout_sec, Tester_Shell_Constants.NETWORK_TIMEOUT_SEC)

        self.__target_set_voltage()
        self.__target_set_frequency()

    def _remote_alive(self, boot_timeout_s: int, net_timeout_s: int):
        conn = self.__target_connect_common(boot_timeout_s, net_timeout_s)
        alive: bool = False
        start = self.timeit.default_timer()

        self.logging.info('Checking if remote is up')

        if conn == None:
            return False
        
        try:
            alive = conn.alive()
            
            self.logging.info('Remote is up')
            time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("Boot time elapsed (seconds): " + time) 

            conn.close()
            return alive
        except:
            conn.close()

    def _remote_execute(self, cmd, cmd_timeout_s: int, net_timeout_s: int, dmesg_index: int, times: int):
        alive = self._remote_alive(self.__boot_timeout_sec, net_timeout_s)
        if (not alive):
            self._ovrd_unused_target_reset_button()

        execution_attempt_counter = 0
        first_error = True

        while True:
            conn = self.__target_connect_common(cmd_timeout_s, net_timeout_s)
            if (conn == None):
                self._ovrd_unused_target_reset_button()

            try:
                start = self.timeit.default_timer()
                obj = conn.root.execute_n_times(cmd, dmesg_index, times)
                data = orjson.loads(obj)
                results_lists = list(data)
                results = []
                # Fix the data accessing issue. Note: When the connection close, the data that has been transfered became unreachable.
                # By typecasting the data to it's original type,we overcome this issue. It seems the type 'rpyc.core.netref.type' has this issue.
                for results_list in results_lists:
                    new_dicts = dict(results_list)
                    results.append(new_dicts)

                time = str(self.math.ceil(self.timeit.default_timer() - start))
                self.logging.info("Remote_execute(" + results[0]["run_command"] + ") elapsed (seconds): " + time)
                for check_result in results:
                    if check_result["return_code"] != '0':
                        self.logging.error("ERROR WHEN RUNNING: " + check_result["run_command"] + " STDERR: " + check_result["stderror"])
                conn.close()
                return results

            except:
                if first_error == True:
                    self._ovrd_clacify_detected_error()
                first_error = False
                conn.close()
                if  execution_attempt_counter > Tester_Shell_Constants.CMD_EXECUTION_ATTEMPT:
                    self._ovrd_unused_target_reset_button()
                    first_error = True
                else:
                    self.logging.warning("Execution timeout. Attempt " + str(execution_attempt_counter))
                execution_attempt_counter += 1

    """
        <--- Implementation dependent methods --->
    """
    def _ovrd_detect_cache_upsets(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass

    def _ovrd_detect_posible_sdcs(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass

    def _ovrd_unused_target_reset_button(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass

    def _ovrd_unused_target_power_button(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass

    def _ovrd_target_is_application_alive(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass

    def _ovrd_clacify_detected_error(self):
        """
            'ovrd_' prefix indicates that this method must be overriden
            by the sub class.
        """
        pass


def main():
    test = Tester_Shell()


if __name__ == '__main__':
    main()