import orjson
import traceback
import rpyc
from time import sleep
import json
from datetime import datetime
import logging
from time import time
import timeit
import math
from datetime import timedelta
import os 
from enum import Enum
import cloudpickle
import rpyc.core
import rpyc.core.stream

#from GPIOClient import GPIOClient


os.environ["PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT"] = "20.0" 

class Tester_Shell_Constants(Enum):
    """
        @attribute PMD_THRESHOLD: This value determines the maximum acceptable power consumption for the PMD.
        @attribute SOC_THRESHOLD: This value determines the maximum acceptable power consumption for the SoC.
        @attribute CURRENT_PMD_THRESHOLD_SCALE: This value determines the factor by which to increase the power consumption threshold of PMD.
        @attribute CURRENT_SOC_THRESHOLD_SCALE: This value determines the factor by which to increase the power consumption threshold for the System-on-Chip (SoC).
        @attribute TIMEOUT_SCALE_BOOT: This value determines the factor by which to increase the boot time threshold.
        @attribute TIMEOUT_SCALE_VOLTAGE: This value determines the factor by which to increase the voltage runtime threshold.
        @attribute TIMEOUT_COLD_CACHE_SCALE_BENCHMARK: This value determines the factor by which to increase the benchmark runtime threshold on the first run.
        @attribute RESET_AFTER_CONCECUTIVE_ERRORS: This value determines the number of consecutive errors that must occur before the experiment system automatically resets.
        @attribute EFFECTIVE_SEC_PER_BATCH: This value determines the allocated time (in seconds) for each batch of benchmarks to run.
        @attribute BENCHMARK_VERIFICATOIN_REGEX: This value specifies the regular expression used to validate the output of a benchmark run. A successful match indicates the benchmark completed correctly.
        @attribute NETWORK_TIMEOUT_SEC: This value specifies the maximum wait time before the host determines that the device under test (DUT) is down. 
        @attribute CMD_EXECUTION_ATTEMPT: This specifies the number of times the host will attempt to execute a command before a reset is required.
    """
    PMD_THRESHOLD                      =  95.0
    SOC_THRESHOLD                      =  95.0
    CURRENT_PMD_THRESHOLD_SCALE        =  1.02
    CURRENT_SOC_THRESHOLD_SCALE        =  1.02
    TIMEOUT_SCALE_BOOT                 =  2.50
    TIMEOUT_SCALE_VOLTAGE              =  1.20
    TIMEOUT_COLD_CACHE_SCALE_BENCHMARK =  4.00
    RESET_AFTER_CONCECUTIVE_ERRORS     =  2.00
    EFFECTIVE_SEC_PER_BATCH            =  20.0
    BENCHMARK_VERIFICATOIN_REGEX       =  r'Verification( +)=(. +.*)'
    NETWORK_TIMEOUT_SEC                =  2.00
    CMD_EXECUTION_ATTEMPT              =  1.00
    UNDERVOLT_POSITIVE_STEP            =  1.00
    UNDERVOLT_NEGATIVE_STEP            = -1.00
    TIMEOUT_SIMPLE_EXECUTION           =  60

class Tester_Shell_Defaults(Enum):
    """
        @attribute FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES: Specifies the total number of minutes required to complete the experiment.
        @attribute FINISH_AFTER_TOTAL_ERRORS: Specifies the total number of errors allowed before the experiment is terminated.
    """
    FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES = 100
    FINISH_AFTER_TOTAL_ERRORS            = 100

class Tester_Shell_Power_Action(Enum):
    """
        This enum is used to control the power and reset buttons of the DUT (Device Under Test).
        
        @attribute TARGET_POWER_BTN_PRESS: Presses the power button of the DUT.
        @attribute TARGET_RESET_BTN_PRESS: Presses the reset button of the DUT.
    """
    TARGET_POWER_BTN_PRESS = 0
    TARGET_RESET_BTN_PRESS = 1

class Tester_Shell_Callback(Enum):
    """
        This enum is used to assign functions that determine the functionality of various callbacks within the host.

        @attribute IS_RESULT_CORRECT: Assign a function to determine the functionality of the is_result_correct callback.
        @attribute DETECT_CACHE_UPSETS: Assign a function to determine the functionality of the detect_cache_upsets callback.
        @attribute TARGET_RESET_BUTTON: Assign a function to determine the functionality of the target_reset_button callback.
        @attribute TARGET_POWER_BUTTON: Assign a function to determine the functionality of the target_power_button callback.
        @attribute TARGET_IS_NETWORK: Assign a function to determine the functionality of the target_is_network callback.
        @attribute DUT_MONITOR: Assign a function to determine the functionality of the dut_monitor callback.
        @attribute ADDITIONAL_LOGS: Assign a function to determine the functionality of the additional_logs callback.
        @attribute UPDATE_ALL: Assign a function to determine the functionality of the update_all callback.
        @attribute ACTIONS_ON_REBOOT: Assign a function to determine the functionality of the actions_on_reboot callback.
    """
    IS_RESULT_CORRECT       = "__callback_is_result_correct"
    DETECT_CACHE_UPSETS     = "__callback_detect_cache_upsets"
    TARGET_RESET_BUTTON     = "__callback_target_reset_button"
    TARGET_POWER_BUTTON     = "__callback_target_power_button"
    DUT_MONITOR             = "__callback_dut_monitor"
    ADDITIONAL_LOGS         = "__callback_additional_logs"
    UPDATE_ALL              = "__callback_update_all"
    ACTIONS_ON_REBOOT       = "__callback_actions_on_reboot"
    UNDERVOLT_FORMAT        = "__callback_unvervolt_format"
    REQUEST_VOLTAGE_VALUE   = "__callback_request_voltage_value"
    DUT_HEALTH_CHECK        = "__callback_dut_health_check"

class Tester_Shell_Health_Status(Enum):
    HEALTHY = 0
    DAMAGED = 1

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
        results["run_counter"] = run_counter 

        self.__batch[str(self.__run)] = results
        self.__run += 1

    def get_batch(self):
        return self.__batch

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
        self.__reset_counter: int       = 0
        self.__run_counter: int         = 0
        self.__sdc_counter: int         = 0 
        self.__total_errors: int        = 0

        # Important dictionaries
        self.__voltage_commands: dict   = {}
        self.__benchmark_commands: dict = {} 
        self.__timeouts: dict = {}
        self.__system_errors_per_benchmark: dict  = {} 
        self.__network_errors_per_benchmark: dict = {}
        self.__batch_per_benchmark: dict = {}
        self.__effective_time_per_batch_s: float = Tester_Shell_Constants.EFFECTIVE_SEC_PER_BATCH.value
        # Important lists
        self.__voltage_list: list   = []
        self.__benchmark_list: list = []

        # Target related
        self.__target_ip: str   = ""
        self.__target_port: str = ""
        
        self.__first_boot: bool = True
        self.__dmesg_index: int = 0
        self.__dmesg_diff: str  = ""

        # Run related
        self.__current_benchmark_id: str = ""
        self.__current_voltage_id: str   = ""
        self.__setup_id: str             = ""

        self.__finish_after_total_effective_min: float = Tester_Shell_Defaults.FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES.value
        self.__finish_after_total_errors: float = Tester_Shell_Defaults.FINISH_AFTER_TOTAL_ERRORS.value

        self.__effective_total_elapsed_min: float = 0
        self.__experiment_total_elapsed_s: float  = 0.1

        self.__experiment_start_time: time = time()

        # Scales
        self.__timeout_scale_benchmark: float      = 0
        self.__benchmark_cold_cache_timeout: float = 0

        # timeouts
        self.__boot_timeout_sec: float       = 0
        self.__voltage_config_timeout: float = 0
        self.__benchmark_timeout: float      = 0

        # Callbacks to be implemented
        self.__callback_is_result_correct: function       = lambda result: None
        self.__callback_detect_cache_upsets: function     = lambda dmesg: None
        self.__callback_target_reset_button: function     = lambda: None
        self.__callback_target_power_button: function     = lambda: None
        self.__callback_dut_monitor: function             = lambda healthlog: None
        self.__callback_additional_logs: function         = lambda: str
        self.__callback_update_all: function              = lambda: None
        self.__callback_actions_on_reboot: function       = lambda: None
        self.__callback_request_voltage_value: function   = lambda: str # TODO - returns a string which represent the current voltage value (undervolt characterization specific)
        self.__callback_unvervolt_format: function        = lambda tester: str # TODO - returns a string which the next voltage (step), in the right format  (undervolt characterization specific)
        self.__callback_dut_health_check: function        = lambda tester: Tester_Shell_Health_Status
        # Debug flags.
        self.__debug_disable_resets: bool = False
        self.__debug_disable_state: bool  = False

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
        self.__timeout_scale_benchmark = 1.5 * self.__batch_per_benchmark[self.__current_benchmark_id] 
        self.__boot_timeout_sec = round(self.__timeouts["BOOT"] * Tester_Shell_Constants.TIMEOUT_SCALE_BOOT.value)
        self.__benchmark_timeout = round(self.__timeout_scale_benchmark * self.__timeouts[self.__current_benchmark_id])
        self.__benchmark_cold_cache_timeout = round(self.__timeouts[self.__current_benchmark_id] * Tester_Shell_Constants.TIMEOUT_COLD_CACHE_SCALE_BENCHMARK.value)

        if (len(self.__voltage_list) > 0):
            self.__voltage_config_timeout = round(self.__timeouts[self.__current_voltage_id] * Tester_Shell_Constants.TIMEOUT_SCALE_VOLTAGE.value)

        #self.__target_set_voltage() Redundunt. See functions: ~ reset_state ~ and ~ power_handler ~.
        self.__callback_update_all()

    def __target_set_voltage(self):
        logging.warning('Configuring voltage: ' + self.__current_voltage_id)
        ret_code: int = self.remote_execute(self.__voltage_commands[self.__current_voltage_id], self.__voltage_config_timeout,
                                              Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, 1, 1, False)[0]["return_code"]
    
        # Ensure that the voltage is applied.
        while int(ret_code) != 0:
            logging.warning('Failed to configure voltage: ' + self.__current_voltage_id)
            logging.warning('Configuring voltage: ' + self.__current_voltage_id)
            ret_code = self.remote_execute(self.__voltage_commands[self.__current_voltage_id], self.__voltage_config_timeout,
                                             Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, 1, 1, False)[0]["return_code"]

    def __generate_result_name(self) -> str:
        now = datetime.now() # current date and time
        result_date = now.strftime("%m_%d_%Y__%H_%M_%S")
        result_file_name = "results/" + self.__setup_id + "_" + self.__current_benchmark_id + "_" + self.__current_voltage_id + "_" + result_date + ".json"

        return result_file_name

    def __target_connect_common(self, excp_timeout_s: int, net_timeout_s: int, ret_imediate: bool) -> rpyc.core.stream.SocketStream:
        sleep_sec_excep: float = 1 
        #conn_count_thresh: int = int(excp_timeout_s / sleep_sec_excep)
        
        remote_down_time_start: time = None # The time that the remote started to not responed 
        remote_down_elapsed: time = None    # How many seconds the remote is down.
        remote_down_down_scale = 1.5

        attemp_counter: int = 0
        first_error: bool = True

        while True:
            try:
                c: rpyc.core.stream.SocketStream = rpyc.connect(self.__target_ip, self.__target_port)
                c._config['sync_request_timeout'] = excp_timeout_s

                if not c.closed:
                    logging.info("Connected to server")
                    return c
            
                return None
            except:
                if (ret_imediate == True):
                    return None

                if first_error == True:
                    self.__clacify_detected_error()
                    remote_down_time_start = time()
                remote_down_elapsed = time() - remote_down_time_start
                first_error = False
                #conn_count_thresh -= 1 
                attemp_counter += 1
                logging.warning('Remote is down..trying to connect. Attempt: ' + str(attemp_counter))
                sleep(sleep_sec_excep)
                #if conn_count_thresh <= 0 or remote_down_elapsed >= (excp_timeout_s * remote_down_down_scale):
                if remote_down_elapsed >= (net_timeout_s * remote_down_down_scale):
                    self.power_handler(Tester_Shell_Power_Action.TARGET_RESET_BTN_PRESS)
                    first_error = True
                    remote_down_time_start = None
                    attemp_counter = 0
                    #conn_count_thresh = int(net_timeout_s / sleep_sec_excep)

    def __save_results(self, batch: Tester_Batch):
        result_name: str = self.__generate_result_name()
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

    def __save_state(self):
        """
            This function preserves the program's current state by transforming the 
            class object into a linear sequence of bytes that can be saved and later loaded.
        """
        if self.__debug_disable_state: return

        filename: str = "state/" + self.__setup_id + "_" + self.__current_benchmark_id + "_" + self.__current_voltage_id + "_state.state"
        try:
            with open(filename, "wb") as serialized_instance:
                cloudpickle.dump(self, serialized_instance)
        except:
            self.logging.warning("Failed to save the current state.")

    def __restore_state(self):
        """
            This function rewinds the Symphony program to a previous state. It 
            achieves this by reversing the process of the save_state
            function
        """
        if self.__debug_disable_state: return

        filename: str = "state/" + self.__setup_id + "_" + self.__current_benchmark_id + "_" + self.__current_voltage_id + "_state.state"
        try:
            with open(filename, "rb") as decirialized_instance:
                prev_state = cloudpickle.load(decirialized_instance)
                self.__dict__.update(prev_state.__dict__)
            # If the experiment is unbervolt related, then ensure that the voltage is set.
            if (len(self.__voltage_list) > 0): self.__target_set_voltage()
        except:
            logging.warning("Failed to load previous state.")

    def __decode_target_response(self, response) -> list:
        """
            @param response
            @returns 
        """
        data = orjson.loads(response)
        conv_to_list: list = list(data)
        results: list = []
        for result in conv_to_list:
            tmp_dict = dict(result)
            results.append(tmp_dict)

        return results

    def __clacify_detected_error(self):
        if (self.__callback_dut_health_check(self) == Tester_Shell_Health_Status.DAMAGED):
            self.__system_errors_per_benchmark[self.__current_benchmark_id] += 1
            logging.warning("System error detected.")
        else:
            self.__network_errors_per_benchmark[self.__current_benchmark_id] += 1
            logging.warning("Network error detected.")

    def __load_optional_attr_from_dict(self, src: dict):
        """
            @param src
        """
        # (OPTIONAL) fields.
        effective_time_per_batch_s: float       = None
        finish_after_total_effective_min: float = None
        finish_after_total_errors: float        = None
        try:
            effective_time_per_batch_s: float       = src["effective_time_per_batch_s"]
            finish_after_total_effective_min: float = src["finish_after_total_effective_min"]
            finish_after_total_errors: float        = src["finish_after_total_errors"]
        except KeyError as e:
            self.__effective_time_per_batch_s       = Tester_Shell_Constants.EFFECTIVE_SEC_PER_BATCH.value
            self.__finish_after_total_effective_min = Tester_Shell_Defaults.FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES.value
            self.__finish_after_total_errors        = Tester_Shell_Defaults.FINISH_AFTER_TOTAL_ERRORS.value
            logging.warning("Unable to load optional attributes. Using defaults instead.")
            logging.warning("Missing value for: " + str(e.args[0]) + " -> (Dictionary/JSON)")

        if (effective_time_per_batch_s != None):
            logging.warning("Setting EFFECTIVE_TIME_PER_BATCH = " + str(effective_time_per_batch_s))
            self.__effective_time_per_batch_s = effective_time_per_batch_s

        if (finish_after_total_effective_min != None):
            logging.warning("Setting FINISH_AFTER_TOTAL_EFFECTIVE_MIN = " + str(finish_after_total_effective_min))
            self.__finish_after_total_effective_min = finish_after_total_effective_min

        if (finish_after_total_errors != None):
            logging.warning("Setting FINISH_AFTER_TOTAL_ERRORS = " + str(finish_after_total_errors))
            self.__finish_after_total_errors = finish_after_total_errors

    def __validate_attr_on_dict(self):
        """
        """
        try:
            [self.__voltage_commands[vid] for vid in self.__voltage_list]
            [self.__benchmark_commands[bid] for bid in self.__benchmark_list]
            [self.__timeouts[vid] for vid in self.__voltage_list]
            [self.__timeouts[bid] for bid in self.__benchmark_list]
        except KeyError as e:
            logging.error("The data on Dictionary/JSON is incomplete")
            logging.error("Incomplete value: " + str(e.args[0]) + " -> Dictionary/JSON")
            logging.error("Ensure the incomplete value is present in the relevant lists and dictionaries.")
            exit(0)        

        for vid in self.__voltage_commands.keys():
            if (vid not in self.__voltage_list or vid not in self.__timeouts):
                logging.error("The data on Dictionary/JSON is incomplete")
                logging.error("Incomplete value: " + vid + " -> Dictionary/JSON")
                logging.error("Ensure the incomplete value is present in the relevant lists and dictionaries.")
                exit(0)        
    
        for bid in self.__benchmark_commands.keys():
            if (bid not in self.__benchmark_list or bid not in self.__timeouts):
                logging.error("The data on Dictionary/JSON is incomplete")
                logging.error("Incomplete value: " + bid + " -> Dictionary/JSON")
                logging.error("Ensure the incomplete value is present in the relevant lists and dictionaries.")
                exit(0)        

    def __experiment_execute_benchmark(self) -> list:
        results: list = []
        last_executed_bench: int = 0

        if self.__first_boot == True:
            self.__first_boot = False
            results = self.remote_execute(self.__benchmark_commands[self.__current_benchmark_id], 
                                          self.__benchmark_cold_cache_timeout, 
                                          Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, 1, 1, False)
            
            self.__dmesg_diff = results[0]["dmesg_diff"]
        else:
            self.__dmesg_index += len(self.__dmesg_diff)
            results = self.remote_execute(self.__benchmark_commands[self.__current_benchmark_id], 
                                          self.__benchmark_timeout, 
                                          Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, 
                                          self.__dmesg_index, 
                                          self.__batch_per_benchmark[self.__current_benchmark_id], False)
            
            last_executed_bench = self.__batch_per_benchmark[self.__current_benchmark_id] - 1
            self.__dmesg_diff = results[last_executed_bench]["dmesg_diff"]

        return results

    def __experiment_execute_actions_for_each_result(self, src: list) -> tuple[int, Tester_Batch]:
        """
            @param src
        """
        curr_result_correct: bool = True
        total_time_passed: float = 0.0
        total_consecutive_errors: int = 0

        batch: Tester_Batch = Tester_Batch()

        for result in src:
            self.__run_counter += 1

            result["voltage_value"] = self.__callback_request_voltage_value(self)
            total_time_passed += (float(result["duration_ms"])/1000)/60  
            curr_result_correct = self.__callback_is_result_correct(result)
            dut_heath_status = self.__callback_dut_health_check(self)

            self.__callback_detect_cache_upsets(result["dmesg_diff"])
            self.__callback_dut_monitor(result["healthlog"])

            if (curr_result_correct == False or dut_heath_status == Tester_Shell_Health_Status.DAMAGED):
                logging.error("Result SDC detected")
                logging.error("Error_consecutive: " + str(total_consecutive_errors))

                total_consecutive_errors += 1
                self.__sdc_counter += 1
                self.__total_errors += 1
            else:
                total_consecutive_errors = 0

            batch.append_run_results(result, curr_result_correct, self.__dmesg_index, self.__run_counter)

            log_str = "Run: " + str(self.__run_counter) + " | Correct: " + str(curr_result_correct) + " | Effect-run-elapsed(ms): " + result["duration_ms"] + " | timestamp: " \
                    + result["timestamp"]

            logging.info(log_str)

        self.__effective_total_elapsed_min += total_time_passed
        return total_consecutive_errors, batch

    def __undervolt_characterization_execute_for_dururation(self, duration_min) -> bool:
        """
            @param duration_min 
        """
        total_duration_s = 0

        while True:
            if (self.__callback_dut_health_check(self) == Tester_Shell_Health_Status.DAMAGED):
                return False
                    
            if (total_duration_s / 60 >= duration_min):
                break

            timer_start = datetime.now()

            results = self.__experiment_execute_benchmark()
            total_errors, curr_batch = self.__experiment_execute_actions_for_each_result(results)

            self.__save_results(curr_batch)
            if (total_errors > 0): 
                return False

            total_duration_s += (datetime.now() - timer_start).seconds

        return True
    
    """
        <--- Methods for every implementation --->
    """
    """
        <--- Public methods for every implemetation --->
    """

    def remote_alive(self, net_timeout_s: int, ret_imediate: bool) -> bool:
        """
            This function verifies if the machine running the experiment is 
            connected and functional. It takes two parameters:

            @param net_timeout_s: This defines a predefined threshold (in seconds) 
                                  for waiting for a network response from the target machine.
        """
        conn = self.__target_connect_common(net_timeout_s, net_timeout_s, ret_imediate)
        alive: bool = False
        logging.info('Checking if remote is up')
        if conn == None:
            return False
        
        try:
            alive = conn.root.alive()
            logging.info('Remote is up')

            conn.close()
        except:
            conn.close()
            alive = False

        return alive

    def remote_execute(self, cmd: str, cmd_timeout_s: int, net_timeout_s: int, dmesg_index: int, times: int, ret_imediate: bool) -> list:
        """
            @param cmd
            @param cmd_timeout_s
            @param net_timeout_s
            @param dmesg_index
            @param times
            @param ret_imediate
        """
        alive = self.remote_alive(net_timeout_s, ret_imediate)
        if (not alive and ret_imediate == True):
            return None
        elif (not alive):
            self.power_handler(Tester_Shell_Power_Action.TARGET_RESET_BTN_PRESS)

        execution_attempt_counter = 0

        while True:
            if (execution_attempt_counter > 0):
                logging.warning("Assessing the target's health due to execution failure.")

            conn = self.__target_connect_common(cmd_timeout_s, net_timeout_s, ret_imediate)
            if (conn == None):
                self.power_handler(Tester_Shell_Power_Action.TARGET_RESET_BTN_PRESS)

            try:
                start = timeit.default_timer()
                response = conn.root.execute_n_times(cmd, dmesg_index, times)
                results: list = self.__decode_target_response(response)
                time = str(math.ceil(timeit.default_timer() - start))
                logging.info("Remote_execute(" + results[0]["run_command"] + ") elapsed (seconds): " + time)
                for check_result in results:
                    if check_result["return_code"] != '0':
                        logging.error("ERROR WHEN RUNNING: " + check_result["run_command"] + " STDERR: " + check_result["stderror"])
                conn.close()
                return results

            except Exception as e:
                conn.close()
                if execution_attempt_counter > Tester_Shell_Constants.CMD_EXECUTION_ATTEMPT.value:
                    self.power_handler(Tester_Shell_Power_Action.TARGET_RESET_BTN_PRESS)
                    execution_attempt_counter = 0
                else:
                    logging.warning("Execution timeout. Attempt " + str(execution_attempt_counter))
                execution_attempt_counter += 1

    def simple_remote_execute(self, cmd: str, times: int, ret_imediate: bool) -> list:
        return self.remote_execute(cmd, Tester_Shell_Constants.TIMEOUT_SIMPLE_EXECUTION.value, 
                                   Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, 0, times, ret_imediate)

    def target_set_next_voltage(self) -> bool:
        """
        """
        curr_vid_index = self.__voltage_list.index(self.__current_voltage_id)
        next_vid_index = curr_vid_index + 1
        if next_vid_index >= len(self.__voltage_list):
            return False
        
        logging.warning("Setting CURRENT_VOLTAGE_ID = " + self.__voltage_list[next_vid_index])
        self.__current_voltage_id = self.__voltage_list[next_vid_index]
        self.__target_set_voltage()
        self.__update()

        return True

    def target_set_next_benchmark(self) -> bool:
        """
        """
        curr_bid_index = self.__benchmark_list.index(self.__current_benchmark_id)
        next_bid_index = curr_bid_index + 1
        if next_bid_index >= len(self.__benchmark_list):
            return False

        logging.warning("Setting CURRENT_BENCHMARK_ID = " + self.__benchmark_list[next_bid_index])
        self.__current_benchmark_id = self.__benchmark_list[next_bid_index]
        self.__update()

        return True

    def load_experiment_attr_from_dict(self, src: dict):
        """
            @param src
        """
        try:
            self.__voltage_commands   = src["voltage_commands"] 
            self.__benchmark_commands = src["benchmark_commands"] 
            self.__timeouts           = src["timeouts"] 
            self.__voltage_list       = src["voltage_list"]
            self.__benchmark_list     = src["benchmark_list"] 
            self.__target_ip          = src["target_ip"]
            self.__target_port        = src["target_port"]
            self.__setup_id           = src["setup_id"]
        except KeyError as e:
            logging.error("Failed to parse dictionary/JSON")
            logging.error("Missing value for: " + str(e.args[0]) + " -> Dictionary/JSON")
            exit(0)
        
        self.__load_optional_attr_from_dict(src)

        # Set initial benchmark and voltage ids.
        self.__current_benchmark_id = self.__benchmark_list[0]
        
        if (len(self.__voltage_list) > 0):
            self.__current_voltage_id   = self.__voltage_list[0]
            logging.warning("Setting CURRENT_VOLTAGE_ID = " + self.__current_voltage_id)

        logging.warning("Setting CURRENT_BENCHMARK_ID = " + self.__current_benchmark_id)

        # Calculate the number of runs per batch for each benchmark.
        # And initialize the system/network errors per benchmark
        for benchmark in self.__benchmark_list:
            self.__batch_per_benchmark[benchmark] = int(math.ceil(self.__effective_time_per_batch_s/self.__timeouts[benchmark]))
            self.__system_errors_per_benchmark[benchmark]  = 0
            self.__network_errors_per_benchmark[benchmark] = 0

        self.__validate_attr_on_dict()
        logging.info("Attributes parsed successfully from dictionary/JSON")
        # Update the attributes of the Tester.
        self.__update()

    def load_experiment_attr_from_json_file(self, src: str):
        with open(src) as json_file:
            json_content: dict = json.load(json_file)
            self.load_experiment_attr_from_dict(json_content)

    def target_perform_undervolt_test(self):
        logging.warning("Start the undervolting process for: " + self.__target_ip)

        self.__target_set_voltage()
        benchmarks_has_next = True
        voltage_has_next    = True
        while voltage_has_next:
            self.experiment_start()

            benchmarks_has_next = self.target_set_next_benchmark()
            if not benchmarks_has_next:
                # Reset benchmarks
                logging.warning("Setting CURRENT_BENCHMARK_ID = " + self.__benchmark_list[0])

                self.__current_benchmark_id = self.__benchmark_list[0]
                voltage_has_next = self.target_set_next_voltage()

    def debug_toggle_resets(self):
        self.__debug_disable_resets = not self.__debug_disable_resets
        if self.__debug_disable_resets == True:
            logging.warning("Disabling resets")
        else:
            logging.warning("Enable resets")

    def debug_toggle_state_restore(self):
        self.__debug_disable_state = not self.__debug_disable_state
        if self.__debug_disable_state == True:
            logging.warning("Disabling state restores/saves")
        else:
            logging.warning("Enable state restore/saves")

    def power_handler(self, action: Tester_Shell_Power_Action):
        """
            This function uses an abstract methodology to achieve power and reset button 
            functionality in an experiment. 
            The specific actions for these buttons are not defined
            here but rather in subclasses. In order for this to work, 
            subclasses must implement the following functions:
                - __callback_target_power_button (Optional)
                - __callback_target_reset_button

            @param action
        """
        if self.__debug_disable_resets == True:
            return

        if action == Tester_Shell_Power_Action.TARGET_POWER_BTN_PRESS:
            self.__callback_target_power_button()
            return

        elif action == Tester_Shell_Power_Action.TARGET_RESET_BTN_PRESS:
            alive = False
            down_time_start: time = None
            down_time_elapsed: time = None
            while not alive:
                self.__reset_counter += 1
                logging.warning("Remote is down..trying to reset")
                self.__callback_target_reset_button()
                logging.warning("Awaiting the DUT to power up")
                alive = False

                down_time_start = time()
                down_time_elapsed = 0

                while (not alive) and (down_time_elapsed < self.__boot_timeout_sec):
                    alive = self.remote_alive(Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, True)
                    down_time_elapsed = time() - down_time_start

            logging.info("Booted")

        # If the experiment is undervolt related, then restore the voltage after the power cycle.
        if (len(self.__voltage_list) > 0): self.__target_set_voltage()
        self.__callback_actions_on_reboot()

    def auto_undervolt_characterization(self, duration_per_bench_min: int, characterization_id: str) -> int:
        """
            @param duration_per_bench_min
        """
        self.debug_toggle_resets()
        logging.warning("Starting undervolting characterization for " + self.__current_benchmark_id)
        logging.warning("Characterization ID: " + characterization_id)
        #vid_steps = 0x0
        safe_voltage = ""

        while True:
            command_to_exec = self.__callback_unvervolt_format() # Retrieve the next command with the user defined step and format
            self.remote_execute(command_to_exec, Tester_Shell_Constants.TIMEOUT_COLD_CACHE_SCALE_BENCHMARK.value, 
                                Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, 0, 1, False)

            logging.warning("Currently examined voltage: " + self.__callback_request_voltage_value(self))
            
            while True:
                logging.warning("Currently examined benchmark: " + self.__current_benchmark_id)
                failure = self.__undervolt_characterization_execute_for_dururation(duration_per_bench_min)

                if not failure:
                    logging.info("Found Vsafe: " + safe_voltage)
                    logging.info("Vcrash: " + self.__callback_request_voltage_value(self))
                    return safe_voltage

                if (self.target_set_next_benchmark() == False): break

            safe_voltage = self.__callback_request_voltage_value(self)

    def experiment_start(self):
        logging.info('Starting... Benchmark: ' + self.__current_benchmark_id)

        error_consecutive: int = 0
        curr_batch: Tester_Batch = Tester_Batch()
        self.__restore_state()

        try:
            while True:
                results_as_list: list = self.__experiment_execute_benchmark()
                error_consecutive, curr_batch = self.__experiment_execute_actions_for_each_result(results_as_list)

                self.__save_results(curr_batch)

                effective_elapsed_min = str("{:.2f}".format(round(self.__effective_total_elapsed_min, 2)))
                self.__experiment_total_elapsed_s = (time() - self.__experiment_start_time)

                log_str = "Resets: " + str(self.__reset_counter) + " | PowerCycles: " + str(self.__power_cycle_counter) \
                          + " | Effective-elapsed(min): " + str(effective_elapsed_min)
                logging.info(log_str)

                log_errors_str = "Total Errors | Network: "+ str(self.__network_errors_per_benchmark[self.__current_benchmark_id]) + \
                                 " | System crash: "+ str(self.__system_errors_per_benchmark[self.__current_benchmark_id]) + \
                                 " | SDCs: "+ str(self.__sdc_counter)
                logging.info(log_errors_str)

                additional_logs = self.__callback_additional_logs()
                logging.info(additional_logs)

                experiment_elapsed_sec_str = str(timedelta(seconds=self.__experiment_total_elapsed_s))
                logging.info("Total elapsed: "+ experiment_elapsed_sec_str + \
                             " (BENCH_ID = " + self.__current_benchmark_id + " | VOLTAGE_ID = " + self.__current_voltage_id + ")")

                if error_consecutive == Tester_Shell_Constants.RESET_AFTER_CONCECUTIVE_ERRORS:
                    logging.warning("Reseting DUT. Error_consecutive: " + str(error_consecutive))
                    self.__total_errors += 1
                    self.power_handler(Tester_Shell_Power_Action.TARGET_RESET_BTN_PRESS)

                self.__save_state()

                if ((self.__effective_total_elapsed_min > self.__finish_after_total_effective_min) \
                    or (self.__total_errors > self.__finish_after_total_errors)):
                    self.__effective_total_elapsed_min = 0
                    self.__finish_after_total_errors = 0
                    break
        except Exception:
            logging.warning(traceback.format_exc())
            pass

    def set_callback(self, callback_func, callback_id: Tester_Shell_Callback):
        """
            @param callback_func 
            @param callback_id
        """
        if (not isinstance(callback_id, Tester_Shell_Callback)):
            logging.error("Error cause: " + str(callback_id))
            logging.error("Error message: No such callback exists")
            exit(0)

        # Assign the callback function to the coresponded function pointer.
        try:
            base_class = self.__class__
            while base_class.__base__.__name__ != "object":
                base_class = base_class.__base__

            internal_name = "_" + base_class.__name__ + callback_id.value
            self.__dict__[internal_name]
        except:
            logging.error("Error cause: " + str(callback_id))
            logging.error("No such callback exists")
            exit(0)

        self.__dict__[internal_name] = callback_func

    def estimate_timeouts(self):
        estimate_start: time = None
        elapsed: time = None

        estimate_start = time()
        logging.warning("Estimate the boot time")
        self.__callback_target_reset_button()
        while not self.remote_alive(Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, True):
            pass
        elapsed = time() - estimate_start

        logging.warning("BOOT TIMEOUT=" + str(math.ceil(elapsed - Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value)))

        logging.warning("Estimate the benchmark execution time.")
        next = True
        while next:
            logging.warning("BENCHMARK=" + self.__current_benchmark_id)
            estimate_start = time()
            self.simple_remote_execute(self.__benchmark_commands[self.__current_benchmark_id], 1, True)
            elapsed = time() - estimate_start
            next = self.target_set_next_benchmark()
            logging.warning("TIMEOUT=" + str(math.ceil(elapsed - Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value)))

        if len(self.__voltage_list) > 0:
            logging.warning("Estimate the benchmark execution time.")
            next = True
            while next:
                logging.warning("VOLTAGE:" + self.__current_voltage_id)
                estimate_start = time()
                self.simple_remote_execute(self.__voltage_commands[self.__current_voltage_id], 1, True)
                elapsed = time() - estimate_start
                next = self.target_set_next_voltage()
                logging.warning("TIMEOUT=" + str(math.ceil(elapsed - Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value)))

    @property
    def current_benchmark_id(self) -> str:
        return self.__current_benchmark_id
    
    @property
    def current_voltage_id(self) -> str:
        return self.__current_voltage_id