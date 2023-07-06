#!/usr/bin/env python
import sys # for exit
import orjson

from GPIOClient import GPIOClient

class Tester:
    import traceback
    import rpyc
    from time import sleep
    import serial
    from serial.tools import list_ports #pyserial, esptool
    import json
    import re
    from datetime import datetime
    import logging
    from time import time
    import timeit
    import math
    from datetime import timedelta
    import os 

    os.environ["PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT"] = "20.0" 

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
        """
        The _update method updates various attributes of the Tester class
        based on the current benchmark ID and voltage ID. It also resets certain
        attributes that are specific to a single run of the test.
        """
        #Global variables
        self.now = self.datetime.now() # current date and time
        self.log_date = self.now.strftime("%m_%d_%Y__%H_%M_%S")
        self.log_file_name = 'logs/log_' + self.log_date + '.log'
        # self.logging.INFO
        self.logging.basicConfig(filename=self.log_file_name, encoding='utf-8', format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s' \
            ,level=self.logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
        # formatter = self.logging.Formatter(fmt='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
        #                       datefmt='%Y-%m-%d,%H:%M:%S')

        screen_handler = self.logging.StreamHandler()
        screen_handler.setFormatter(self.CustomFormatter())
        self.logging.getLogger().addHandler(screen_handler)

        regex = r'Verification( +)=(. +.*)'
        self.verification_regex = self.re.compile(regex, self.re.IGNORECASE)
        
        regex = r'SVI2_P_Core:\s+(\d+\.\d+)'
        self.power_pmd_regex = self.re.compile(regex, self.re.IGNORECASE)

        regex = r'SVI2_P_SoC:\s+(\d+\.\d+)'
        self.power_soc_regex = self.re.compile(regex, self.re.IGNORECASE)

        regex = r'SVI2_Core:\s+(\d+\.\d+)'
        self.voltage_pmd_regex = self.re.compile(regex, self.re.IGNORECASE)

        regex = r'SVI2_SoC:\s+(\d+\.\d+)'
        self.voltage_soc_regex = self.re.compile(regex, self.re.IGNORECASE)

        regex = r'Tdie:\s+.(\d+\.\d+)'
        self.temp_regex = self.re.compile(regex, self.re.IGNORECASE)

        self.power_cycle_counter = 0
        self.reset_counter = 0

        self.run_counter = 0
        self.effective_total_elapsed_minutes = 0
        self.sdc_counter = 0 
        self.experiment_total_elapsed_sec = 0.0
        self.experiment_start_time = self.time()    

        self.first_boot = True
        self.dmesg_index = 0
        self.dmesg_diff = ""

        # CONSTANTS
        # check https://github.com/gtcasl/hpc-benchmarks/blob/master/NPB3.3/NPB3.3-MPI/
        self.benchmarks_list = ["FT", "MG", "CG", "IS", "LU", "EP"]
        self.benchmark_commands = {
            "FT" : '/usr/lib64/openmpi/bin/mpirun --oversubscribe -np 16 /home/eslab/bench/NPB2.4.1/NPB2.4-MPI/bin/ft.A.16',
            "MG" : '/usr/lib64/openmpi/bin/mpirun --oversubscribe -np 16 /home/eslab/bench/NPB2.4.1/NPB2.4-MPI/bin/mg.A.16',
            "CG" : '/usr/lib64/openmpi/bin/mpirun --oversubscribe -np 16 /home/eslab/bench/NPB2.4.1/NPB2.4-MPI/bin/cg.A.16',
            "IS" : '/usr/lib64/openmpi/bin/mpirun --oversubscribe -np 16 /home/eslab/bench/NPB2.4.1/NPB2.4-MPI/bin/is.A.16',
            "LU" : '/usr/lib64/openmpi/bin/mpirun --oversubscribe -np 16 /home/eslab/bench/NPB2.4.1/NPB2.4-MPI/bin/lu.A.16',
            "EP" : '/usr/lib64/openmpi/bin/mpirun --oversubscribe -np 16 /home/eslab/bench/NPB2.4.1/NPB2.4-MPI/bin/ep.A.16'
        }
        
        self.voltage_list = ["VID21", "VID36", "VID37", "VID38", "VID39"]
        self.voltage_commands = {
            "VID39" : 'sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 39',
            "VID38" : 'sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 38',
            "VID37" : 'sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 37', 
            "VID36" : 'sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 36',
            "VID21" : 'sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 21'  
        }

        self.LOWER_FREQUENCY_ID = "84"
        self.LOWER_FREQUENCY_DID = "C"
        self.SET_LOWER_FREQUENCY = False

        #HDD
        self.timeouts = {
            "BOOT" : 51, 
            "MG" : 4,
            "CG" : 3,
            "FT" : 4,
            "IS" : 3,
            "LU" : 8,
            "EP" : 3,
            "VID39" : 3, 
            "VID38" : 3,
            "VID37" : 3,
            "VID36" : 3,
            "VID21" : 3
        }
 
        self.CURRENT_BENCHMARK_ID = "MG"
        self.CURRENT_VOLTAGE_ID = "VID21"
        self.BATCH = 1 # How many times to run a benchmark.
        self.FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES = 100
        self.FINISH_AFTER_TOTAL_ERRORS = 100 
        self.TIMEOUT_SCALE_BENCHMARK = 2 * self.BATCH # TODO - check it again. 
        self.TIMEOUT_SCALE_BOOT = 1.1
        self.TIMEOUT_COLD_CACHE_SCALE_BENCHMARK = 4.0 
        self.TIMEOUT_SCALE_VOLTAGE = 1.2
        self.RESET_AFTER_CONCECUTIVE_ERRORS = 2
        # The DUT power cycles after (RESET_AFTER_CONCECUTIVE_ERRORS + 1)
       
        self.CURRENT_PMD_THRESHOLD = 100  
        self.CURRENT_SOC_THRESHOLD = 100 
        self.TEMP_PMD_THRESHOLD = 90

        self.CURRENT_PMD_THRESHOLD_SCALE = 1.02
        self.CURRENT_SOC_THRESHOLD_SCALE = 1.02
        self.TEMP_PMD_THRESHOLD_SCALE = 1.1

        self.current_pmd_threshold_max = 0 
        self.current_soc_threshold_max = 0 
        self.temp_pmd_threshold_max = 0 

        self.EXECUTION_ATTEMPT = 1
        self.NETWORK_TIMEOUT_SEC = 2

        self.TARGET_IP = "10.30.0.67"
        self.TARGET_PORT = 18861 

        self.GPIO_HOST_IP = "10.30.0.63"
        self.GPIO_HOST_PORT = 18861

        self.POWER_RELAY_ID = 1
        self.RESET_RELAY_ID = 2

        self.SET_UP_ID = 0

        #DEBUG
        self.DISABLE_RESET = False
        self.SAVE_THRESHOLDS = True

        #DON'T TOUCH

        self.BENCHMARK_COMMAND = self.benchmark_commands[self.CURRENT_BENCHMARK_ID]
        self.COMMAND_VOLTAGE = self.voltage_commands[self.CURRENT_VOLTAGE_ID]
        self.BOOT_TIMEOUT_SEC = round(self.timeouts["BOOT"] * self.TIMEOUT_SCALE_BOOT)
        self.VOLTAGE_CONFIG_TIMEOUT = round(self.timeouts[self.CURRENT_VOLTAGE_ID] * self.TIMEOUT_SCALE_VOLTAGE)
        self.BENCHMARK_TIMEOUT = round(self.timeouts[self.CURRENT_BENCHMARK_ID] * self.TIMEOUT_SCALE_BENCHMARK)
        self.BENCHMARK_COLD_CACHE_TIMEOUT = round(self.timeouts[self.CURRENT_BENCHMARK_ID] \
            * self.TIMEOUT_COLD_CACHE_SCALE_BENCHMARK)
        self.DMESG_TIMEOUT = 10
    
    def _update(self):
        """
        The _update method updates various attributes of the Tester class
        based on the current benchmark ID and voltage ID. It also resets certain
        attributes that are specific to a single run of the test.
        """
        self.BENCHMARK_COMMAND = self.benchmark_commands[self.CURRENT_BENCHMARK_ID]
        self.COMMAND_VOLTAGE = self.voltage_commands[self.CURRENT_VOLTAGE_ID]
        self.BOOT_TIMEOUT_SEC = round(self.timeouts["BOOT"] * self.TIMEOUT_SCALE_BOOT)
        self.VOLTAGE_CONFIG_TIMEOUT = round(self.timeouts[self.CURRENT_VOLTAGE_ID] * self.TIMEOUT_SCALE_VOLTAGE)
        self.BENCHMARK_TIMEOUT = round(self.timeouts[self.CURRENT_BENCHMARK_ID] * self.TIMEOUT_SCALE_BENCHMARK)
        self.BENCHMARK_COLD_CACHE_TIMEOUT = round(self.timeouts[self.CURRENT_BENCHMARK_ID] \
            * self.TIMEOUT_COLD_CACHE_SCALE_BENCHMARK)
        self.DMESG_TIMEOUT = 10

        self.first_boot = True
        self.dmesg_index = 1
        self.dmesg_diff = ""
        self.current_pmd_threshold_max = 0 
        self.current_soc_threshold_max = 0 
        self.temp_pmd_threshold_max = 0 

        self.power_cycle_counter = 0
        self.reset_counter = 0

        self.run_counter = 0
        self.effective_total_elapsed_minutes = 0
        self.sdc_counter = 0 
        self.experiment_total_elapsed_sec = 0.0
        self.experiment_start_time = self.time()    

        self.restore_thresholds()    

    def set_benchmark_voltage_id(self, id_str, voltage_id_str):
        """
        Set the benchmark and voltage IDs to the provided strings, and log these changes.
        Args:
            id_str (str): The new benchmark ID to set.
            voltage_id_str (str): The new voltage ID to set.
        """
        self.logging.warning("Setting CURRENT_BENCHMARK_ID = " + id_str)
        self.CURRENT_BENCHMARK_ID = id_str
        self.logging.warning("Setting CURRENT_VOLTAGE_ID = " + voltage_id_str)
        self.CURRENT_VOLTAGE_ID = voltage_id_str
        self._update()

    def set_finish_after_effective_minutes_or_total_errors(self, finish_after_effective_min, finish_after_total_errors):
            self.logging.warning("Setting RUNS_PER_TEST = " + str(finish_after_effective_min))
            self.FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES = finish_after_effective_min
            self.FINISH_AFTER_TOTAL_ERRORS = finish_after_total_errors
    
    def enalbe_lower_frequency(self):
        self.SET_LOWER_FREQUENCY = True

    def set_to_lower_frequency(self):
        command_freq_id = "sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --fid {FID}"
        command_div_id = "sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --did {DID}"
        command_freq_id.format(FID = self.LOWER_FREQUENCY_ID)
        command_div_id.format(DID = self.LOWER_FREQUENCY_DID)

        self.logging.info('Configuring frequency: ' + command_freq_id)
        results_freq_id = self.remote_execute(command_freq_id, self.VOLTAGE_CONFIG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1, 1)[0]
        results_div_id = self.remote_execute(command_div_id, self.VOLTAGE_CONFIG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1, 1)[0]

        if results_freq_id["return_code"] != '0' or results_div_id["return_code"] != 0:
             self.logging.warning('Failed to configure lower frequency...')

    def get_voltage_list(self):
        return self.voltage_list
    
    def get_benchmarks_list(self):
        return self.benchmarks_list

    def debug_reset_disable(self):
        """
        Disable the reset functionality for debugging purposes.
        """
        self.DISABLE_RESET = True
    def debug_set_high_timeouts(self):
        """
        Set high timeouts for debugging purposes.
        """
        self.timeouts = {
            "BOOT" : 300, 
            "MG" : 300,
            "CG" : 300,
            "FT" : 300, 
            "IS" : 300,
            "LU" : 300,
            "EP" : 300,
            "VID39" : 300, 
            "VID38" : 300,
            "VID37" : 300,
            "VID36" : 300,
            "VID21" : 300
        }
        self.logging.warning("debug_set_high_timeouts")
        
    def power_cycle(self, count_enable):
        """
        Power cycle the TARGET BOARD, and optionally increment the power cycle counter.
        Args:
            count_enable (bool): Whether to increment the power cycle counter.
        """
        self.first_boot = True
        self.dmesg_diff = 1

        try:
            client = GPIOClient(self.GPIO_HOST_IP, self.GPIO_HOST_PORT)
            client.connect()

            client.turn_on(self.RESET_RELAY_ID)
            self.sleep(2)
            client.turn_off(self.RESET_RELAY_ID)

            client.disconnect()
        except:
            self.logging.error("Remote GPIO is down...")

        if count_enable == True:
            self.power_cycle_counter += 1
        self.logging.warning("Power Cycle")
        if self.remote_alive(self.BOOT_TIMEOUT_SEC):
            self.logging.info("Booted")
            self.set_voltage()
            

    def power_button(self):
        """
        Simulate pressing the power button on the TARGET BOARD.
        """
        self.first_boot = True
        self.dmesg_diff = 1

        try:
            client = GPIOClient(self.GPIO_HOST_IP, self.GPIO_HOST_PORT)
            client.connect()

            client.turn_on(self.POWER_RELAY_ID)
            self.sleep(2)
            client.turn_off(self.POWER_RELAY_ID)
            client.disconnect()
        except:
            self.logging.error("Remote GPIO is down...")

    def reset_button(self):
        """
        Simulate pressing the reset button on the TARGET BOARD, 
        and increment the reset counter.
        """
        self.first_boot = True
        self.dmesg_index = 1

        try:
            client = GPIOClient(self.GPIO_HOST_IP, self.GPIO_HOST_PORT)
            client.connect()

            client.turn_on(self.RESET_RELAY_ID)
            self.sleep(2)
            client.turn_off(self.RESET_RELAY_ID)
            client.disconnect()
        except:
            self.logging.error("Remote GPIO is down...")

        self.reset_counter +=1
        self.logging.warning('Reset')
        if self.remote_alive(self.BOOT_TIMEOUT_SEC):
            self.logging.info("Booted")
            self.set_voltage()
            
    def get_dmesg(self):
        """
        Get the dmesg logs from the TARGET BOARD.
        Returns:
            str: The dmesg logs.
        """
        results = self.remote_execute("date", self.DMESG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1, 1)[0] 
        return results["dmesg_diff"]

    def set_voltage(self):
        """
        Set the voltage of the TARGET BOARD to the value specified by COMMAND_VOLTAGE.
        """
        self.logging.info('Configuring voltage: ' + self.COMMAND_VOLTAGE)
        results = self.remote_execute(self.COMMAND_VOLTAGE, self.VOLTAGE_CONFIG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1, 1)[0]
        if results["return_code"] != '0':
            self.logging.warning('Return error code: ' + results["return_code"] + ' Configuring voltage: ' + self.COMMAND_VOLTAGE)


    def remote_alive(self, boot_timeout_sec: int):
        """
        Check if the remote server is alive.
        Args:
            boot_timeout_sec (int): The number of seconds to wait for the server to boot before giving up.
        Returns:
            bool: True if the server is alive, False otherwise.
        """
        start = self.timeit.default_timer()
        self.logging.info('Checking if remote is up')
        alive = False
        sleep_sec_excep = 0.5 
        conn_count_thresh =  int(boot_timeout_sec / sleep_sec_excep)
        attemp_counter = 0
        while True:
            try:
                c = self.rpyc.connect(self.TARGET_IP, self.TARGET_PORT)
                c._config['sync_request_timeout'] = boot_timeout_sec
                if not c.closed:
                    self.logging.info("Connected to server")
                    try:
                        alive = c.root.alive()
                        c.close() 
                        self.logging.info('Remote is up')
                        time = str(self.math.ceil(self.timeit.default_timer() - start))
                        self.logging.info("Boot time elapsed (seconds): " + time) 
                        return alive 
                    except:
                        c.close()   
            except:
                conn_count_thresh -= 1 
                attemp_counter += 1
                self.logging.warning('Remote is down..trying to connect. Attempt: ' + str(attemp_counter))
                self.sleep(sleep_sec_excep)
                if conn_count_thresh <=0:
                    self.power_cycle(True)
                    conn_count_thresh =  int(boot_timeout_sec / sleep_sec_excep)
                pass
        
    def remote_execute(self, command:str, command_timeout_sec:int, network_timout_sec: int, dmesg_index:int, times:int):
        """
        Execute a command on the remote server.
        Args:
            command (str): The command to execute.
            command_timeout_sec (int): The number of seconds to wait for the command to complete before timing out.
            network_timout_sec (int): The number of seconds to wait for a network response before timing out.
            dmesg_index (int): The index of the dmesg log to return, i.e., resurns dmesg[dmesg_index: end_of(dmesg)]
            times (int): How many times to execute the command.
        Returns:
            tuple: A tuple containing the health log, run command, timestamp, power, temperature, voltage, frequency, duration, standard output, standard error, return code, and dmesg diff.
        """
        sleep_sec_excep = 0.5 
        conn_count_thresh =  int(network_timout_sec / sleep_sec_excep)
        attemp_counter = 0
        execution_attempt_counter = 1
        while True:
            try:
                c = self.rpyc.connect(self.TARGET_IP, self.TARGET_PORT)
                c._config['sync_request_timeout'] = command_timeout_sec
                if not c.closed:
                    self.logging.info("Connected to server")
                    try:
                        start = self.timeit.default_timer()
                        obj = c.root.execute_n_times(command, dmesg_index, times)
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
                        c.close() 
                        return results
                    except TimeoutError as e:
                        self.logging.error(e)
                        self.reset_button()
                        c.close()
                    except Exception as e:
                        self.logging.error(e)
                        c.close()
                        if  execution_attempt_counter > self.EXECUTION_ATTEMPT:
                            self.reset_button()
                        else:
                            self.logging.warning("Execution timeout. Attempt " + str(execution_attempt_counter))
                        execution_attempt_counter += 1
            except Exception as e:
                self.logging.error(e)
                conn_count_thresh -= 1 
                attemp_counter += 1
                self.logging.warning('Remote is down..trying to connect. Attempt: ' + str(attemp_counter))
                self.sleep(sleep_sec_excep)
                if conn_count_thresh <= 0:
                    self.reset_button()
                    conn_count_thresh =  int(network_timout_sec / sleep_sec_excep)
  
    def save_result(self, results, run_counter, correct):
        """
        Save the results of a command execution on the TARGET BOARD.
        Args:
            healthlog (str): The health log from the command execution.
            run_counter (int): The number of times the command has been run.
            run_command (str): The command that was run.
            timestamp (str): The timestamp when the command was run.
            duration_ms (int): The duration of the command execution in milliseconds.
            stdoutput (str): The standard output from the command execution.
            stderror (str): The standard error from the command execution.
            return_code (int): The return code from the command execution.
            dmesg_diff (str): The difference in the dmesg logs before and after the command execution.
        """
        now = self.datetime.now() # current date and time
        result_date = now.strftime("%m_%d_%Y__%H_%M_%S")
        result_file_name = 'results/' + self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_" + result_date + '.json'
        result = {
                    "timestamp" : results["timestamp"],
                    "run_command": results["run_command"],
                    "return_code" : results["return_code"],
                    "run_counter" : run_counter, 
                    "correct" : correct,
                    "duration_ms" : results["duration_ms"],
                    "stdoutput" : results["stdoutput"],
                    "stderror" : results["stderror"],
                    "dmesg_diff" : results["dmesg_diff"],
                    "healthlog" : results["healthlog"],
                    "dmesg_index" : str(self.dmesg_index)
        }
        with open(result_file_name, "w") as json_file:
            self.json.dump(result, json_file)
            
    def save_state(self):
        """
        This function saves the state of the experiment to a JSON file.
        This state includes reset counter, power cycle counter, elapsed minutes, 
        SDC (silent data corruption) counter, run counter, and total elapsed seconds.
        """
        filename = self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_state.json"
        state_file = "./state/" + filename
        state = {
                    "reset_counter": str(self.reset_counter),
                    "power_cycle_counter" : str(self.power_cycle_counter) ,
                    "effective_total_elapsed_minutes" : str(self.effective_total_elapsed_minutes), 
                    "sdc_counter" : str(self.sdc_counter),
                    "run_counter" : str(self.run_counter),
                    "experiment_total_elapsed_sec" : str(self.experiment_total_elapsed_sec)
        }
        try:
            with open(state_file, "w") as json_file:
                self.json.dump(state, json_file)
        except Exception as e:
            self.logging.warning(e)

    def restore_state(self):
        """
        This function restores the state of the experiment from a JSON file.
        If the file is not found, a warning is logged.
        """
        filename = self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_state.json"
        state_file = "./state/" + filename
        try:
            with open(state_file, 'r') as json_file:
                state = self.json.load(json_file)
                self.reset_counter = int(state["reset_counter"])
                self.power_cycle_counter = int(state["power_cycle_counter"])
                self.effective_total_elapsed_minutes = float(state["effective_total_elapsed_minutes"])
                self.sdc_counter = int(state["sdc_counter"])
                self.run_counter = int(state["run_counter"])
                self.experiment_total_elapsed_sec = float(state["experiment_total_elapsed_sec"])
        except Exception:
            self.logging.warning(state_file + " file not found") 
            pass
    
    def save_thresholds(self):
        """
        This function saves the current thresholds to a JSON file.
        """
        filename = self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_thresholds.json"
        directory = "./config/" + str(self.SET_UP_ID)
        threshold_file = "./config/" + str(self.SET_UP_ID) + "/" + filename

        try:
            self.os.mkdir(directory)
        except:
            pass

        threshold = {
            "current_pmd_threshold_max": str(self.current_pmd_threshold_max),
            "current_soc_threshold_max" : str(self.current_soc_threshold_max),
            "temp_pmd_threshold_max" : str(self.temp_pmd_threshold_max),
        }
        try:
            with open(threshold_file, "w") as json_file:
                self.json.dump(threshold, json_file)
        except Exception as e:
            self.logging.warning(e)
    
    def restore_thresholds(self):
        """
        Restores the thresholds from a JSON file. If the file is not found, a warning is logged.
        """
        filename = self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_thresholds.json"
        threshold_file = "./config/" + str(self.SET_UP_ID) + "/" + filename
        try:
            with open(threshold_file, 'r') as json_file:
                threshold = self.json.load(json_file)
                self.CURRENT_PMD_THRESHOLD = float(threshold["current_pmd_threshold_max"]) * self.CURRENT_PMD_THRESHOLD_SCALE
                self.CURRENT_SOC_THRESHOLD = float(threshold["current_soc_threshold_max"]) * self.CURRENT_SOC_THRESHOLD_SCALE
                self.TEMP_PMD_THRESHOLD = self.math.ceil(int(threshold["temp_pmd_threshold_max"]) * self.TEMP_PMD_THRESHOLD_SCALE)
                
                self.logging.warning("Setting CURRENT_PMD_THRESHOLD = " + str(self.CURRENT_PMD_THRESHOLD))
                self.logging.warning("Setting CURRENT_SOC_THRESHOLD = " + str(self.CURRENT_SOC_THRESHOLD))
                self.logging.warning("Setting TEMP_PMD_THRESHOLD = " + str(self.TEMP_PMD_THRESHOLD))
        except Exception as e:
            self.logging.warning(e)
    
    def save_setup_informations(self):
        if self.SET_LOWER_FREQUENCY == False:
            filename = "setup_" + str(self.SET_UP_ID) + ".json"
        else:
            filename = "setup_" + str(self.SET_UP_ID) + "_lower_freq.json"
        set_up_file = "./config/" + filename

        set_up_info = {
            "voltage_list": self.voltage_list,
            "voltage_commands": self.voltage_commands,
            "timeouts": self.timeouts,
            "current_pmd_threshold": self.CURRENT_PMD_THRESHOLD,
            "current_soc_threshold": self.CURRENT_SOC_THRESHOLD,
            "power_relay_id": self.POWER_RELAY_ID,
            "reset_relay_id": self.RESET_RELAY_ID
        }

        try:
            with open(set_up_file, "w") as json_file:
                self.json.dump(set_up_info, json_file, indent=2)
        except Exception as e:
            self.logging.warning(e)

    def get_setup_informations(self):
        if self.SET_LOWER_FREQUENCY == False:
            filename = "setup_" + str(self.SET_UP_ID) + ".json"
        else:
            filename = "setup_" + str(self.SET_UP_ID) + "_lower_freq.json"
        set_up_file = "./config/" + filename

        try:
            with open(set_up_file, 'r') as json_file:
                set_up_info = self.json.load(json_file)
                self.voltage_list = set_up_info["voltage_list"]
                self.voltage_commands = set_up_info["voltage_commands"]
                self.timeouts = set_up_info["timeouts"]
                self.CURRENT_PMD_THRESHOLD = set_up_info["current_pmd_threshold"]
                self.CURRENT_SOC_THRESHOLD = set_up_info["current_soc_threshold"]
                self.POWER_RELAY_ID = set_up_info["power_relay_id"]
                self.RESET_RELAY_ID = set_up_info["reset_relay_id"]

                self.logging.warning("Getting SETUP " + str(self.SET_UP_ID) + " informations")
        except Exception as e:
            self.logging.warning(e)

    def is_result_correct(self, result):
        """
        Checks if the result of the benchmarking test is "SUCCESSFUL". If there is an exception 
        during this check, it logs the error and returns False.
        """
        try:
            verification_str = self.verification_regex.findall(result)
            answer = str(verification_str[0][1])
            answer = answer.strip()
            if answer == "SUCCESSFUL":
                return True
            else:
                return False
        except Exception:
            self.logging.error("Regexpr output: " + answer)
            return False

    def get_timeouts(self):
        """
        Calculates and logs the time taken for various tasks such as booting, voltage configuration,
        and running benchmarks. If an exception occurs, it logs the exception.
        """
        try:
            client = GPIOClient(self.GPIO_HOST_IP, self.GPIO_HOST_PORT)
            client.connect()

            client.turn_on(self.RESET_RELAY_ID)
            self.sleep(2)
            client.turn_off(self.RESET_RELAY_ID)
            client.disconnect()
        except:
            self.logging.error("Remote GPIO is down...")

        try:
            start = self.timeit.default_timer()
            self.remote_alive(self.BOOT_TIMEOUT_SEC)
            time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("boot_time: " + time)

            self.COMMAND_VOLTAGE = "sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 21" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time VID21: " + voltage_config_time)

            self.COMMAND_VOLTAGE = "sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 38" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time VID38: " + voltage_config_time)

            self.COMMAND_VOLTAGE = "sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 39" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time VID39: " + voltage_config_time)

            self.COMMAND_VOLTAGE = "sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 40" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time VID40: " + voltage_config_time)

            start = self.timeit.default_timer()
            self.remote_execute(self.BENCHMARK_COMMAND, 100, self.NETWORK_TIMEOUT_SEC, 1, 1)
            time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("benchmark_time VID40 " + self.CURRENT_BENCHMARK_ID + ":" + time)

            for item in self.benchmarks_list:
                self.CURRENT_BENCHMARK_ID = item
                self.BENCHMARK_COMMAND = self.benchmark_commands[self.CURRENT_BENCHMARK_ID]
                start = self.timeit.default_timer()
                self.remote_execute(self.BENCHMARK_COMMAND, 100, self.NETWORK_TIMEOUT_SEC, 1, 1)
                time = str(self.math.ceil(self.timeit.default_timer() - start))
                self.logging.info("benchmark_time VID40 " + self.CURRENT_BENCHMARK_ID + ":" + time)

            self.COMMAND_VOLTAGE = "sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid 41" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time VID41: " + voltage_config_time)

        except Exception as e:
            self.logging.warning(e)

    def parse_monitor_data(self, healthlog):
        """
        Parses the data from the monitoring tools and logs the current power, voltage, and temperature 
        values. It also checks if any of these values exceed their respective thresholds, and logs a 
        critical message if they do. If an exception occurs during parsing, it logs the exception.
        """
        try:
            power_pmd_str = self.power_pmd_regex.search(healthlog)
            power_soc_str = self.power_soc_regex.search(healthlog)
            voltage_pmd_str = self.voltage_pmd_regex.search(healthlog)
            voltage_soc_str = self.voltage_soc_regex.search(healthlog)
            temp_str = self.temp_regex.search(healthlog)

            power_pmd = float(power_pmd_str.group(1))
            power_soc = float(power_soc_str.group(1))

            voltage_pmd = float(voltage_pmd_str.group(1))
            voltage_soc = float(voltage_soc_str.group(1))
            
            current_pmd = round((power_pmd / (voltage_pmd)),2)
            current_soc = round((power_soc / (voltage_soc)),2)

            temp_pmd = float(temp_str.group(1))
    
            power_curr_volt_temp_str = "MONITOR: PMD = "+ str(power_pmd) + "(W)/" + str(current_pmd) + "(A)/" + str(voltage_pmd) +"(V)/" \
                + str(temp_pmd)+"(C) | SoC = "+ str(power_soc) + "(W)/" + str(current_soc) + "(A)/" + str(voltage_soc) +"(V)/"

            self.logging.info(power_curr_volt_temp_str)
            
            if current_pmd > self.current_pmd_threshold_max:
                self.current_pmd_threshold_max = current_pmd

            if current_soc > self.current_soc_threshold_max:
                self.current_soc_threshold_max = current_soc

            if temp_pmd > self.temp_pmd_threshold_max:
                self.temp_pmd_threshold_max = temp_pmd
            
            if self.SAVE_THRESHOLDS == True:
                self.save_thresholds()

            max_power_curr_volt_temp_str = "MONITOR(MAX): PMD = " + str(self.current_pmd_threshold_max) + "(A)/" + str(voltage_pmd) +"(V)/" \
                + str(self.temp_pmd_threshold_max)+"(C) | SoC = " + str(self.current_soc_threshold_max) + "(A)/"
            
            self.logging.info(max_power_curr_volt_temp_str)

            if current_pmd > self.CURRENT_PMD_THRESHOLD:
                self.logging.critical("PMD overcurrent: " + str(current_pmd) + "(A)")
            
            if current_soc > self.CURRENT_SOC_THRESHOLD:
                self.logging.critical("SOC overcurrent: " + str(current_soc) + "(A)")

            if temp_pmd > self.TEMP_PMD_THRESHOLD:
                self.logging.critical("PMD over temperature: " + str(temp_pmd) + "(C)")
            
        except Exception as e:
            self.logging.warning(e)
    
    def experiment_start(self):
        """
        This method initiates an experiment run, and includes all steps required for
        a full experiment, including initialization, running the benchmark, error 
        checking, logging, data parsing, resetting and power cycling if necessary, 
        and saving the state. 

        It also handles exceptions and ensures continuous running of experiments 
        until the predetermined conditions are met (e.g., a certain number of 
        errors have occurred or a certain amount of time has elapsed).

        The method uses a variety of class attributes to manage the experiment, 
        including timers, counters, flags, thresholds, and command strings.

        A rough idea of the flow is given below:

        Start experiment: 
            Initialize variables (experiment_elapsed_sec_str, error_consecutive), log the start of the experiment, and restore any saved state.

        Main loop:

            The experiment continuously loops until a break condition is met.
            It checks if it's the first boot of the system. If true, it sets first_boot to false and executes the benchmark command with a cold cache timeout.
            If it's not the first boot, it increments the dmesg_index by the length of dmesg_diff, then runs the benchmark command with a regular timeout.
            It increments run_counter and updates the total elapsed time.
            It checks if the result of the command is correct. If not, it logs an error, increments the consecutive error and SDC counters. If the result is correct, it resets the consecutive error counter.
            It logs the result of the run and the current status of the experiment.
            It updates the total elapsed time of the experiment and logs it.
            It parses monitor data.
            If the consecutive error count reaches a threshold, it resets the DUT (Device Under Test). If the consecutive error count exceeds the threshold, it power cycles the DUT.
            It saves the current state of the experiment.
            If the total effective elapsed minutes exceed a threshold or the sum of reset and power cycle counts exceeds a threshold, it breaks the loop.
        End of experiment: 
            Log the end of the experiment.

        Exception handling: 
            If an exception occurs during the experiment, it logs the traceback and continues.
        """
        experiment_elapsed_sec_str = ""
        self.logging.info('Starting... Benchmark: ' + self.BENCHMARK_COMMAND)
        
        self.power_cycle(False)
        
        error_consecutive = 0

        self.restore_state()

        try:
            while True:
                #command:str, command_timeout_sec:int, network_timout_sec: int, dmesg_index:int)
                
                if self.first_boot == True:
                    if self.SET_LOWER_FREQUENCY == True:
                        self.set_to_lower_frequency()
                        self.set_benchmark_voltage_id(self.CURRENT_BENCHMARK_ID, self.CURRENT_VOLTAGE_ID)
                    self.first_boot = False
                    results = self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_COLD_CACHE_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1, 1)
                    self.dmesg_diff = results[0]["dmesg_diff"]
                else:
                    self.dmesg_index += len(self.dmesg_diff)
                    results = self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_TIMEOUT, self.NETWORK_TIMEOUT_SEC, self.dmesg_index, self.BATCH)    
                    self.dmesg_diff = results[self.BATCH - 1]["dmesg_diff"]
                

                for result in results:
                    self.run_counter += 1 
                    self.effective_total_elapsed_minutes += (float(result["duration_ms"])/1000)/60          
                    correct = self.is_result_correct(result["stdoutput"])
                    self.save_result(result, str(self.run_counter), str(correct))

                    if correct == False:
                        self.logging.error("Result SDC detected")
                        self.logging.error("Error_consecutive: " + str(error_consecutive))
                        error_consecutive += 1
                        self.sdc_counter += 1
                    else:
                        error_consecutive = 0   
                    
                    log_str = "Run: " + str(self.run_counter) + " | Correct: " + str(correct) + " | Effect-run-elapsed(ms): " + result["duration_ms"] + " | timestamp: " \
                            + result["timestamp"]
                    self.logging.info(log_str)

                    self.parse_monitor_data(result["healthlog"])

                effective_elapsed_min = str("{:.2f}".format(round(self.effective_total_elapsed_minutes, 2)))

               
                log_str = "Resets: " + str(self.reset_counter) + " | PowerCycles: " + str(self.power_cycle_counter) \
                    + " | Effective-elapsed(min): " + str(effective_elapsed_min) +  " | SDCs: " +  str(self.sdc_counter)
                self.logging.info(log_str)

                self.experiment_total_elapsed_sec = (self.time() - self.experiment_start_time)
                experiment_elapsed_sec_str = str(self.timedelta(seconds=self.experiment_total_elapsed_sec))
                self.logging.info("Total elapsed: "+ experiment_elapsed_sec_str + \
                    " (BENCH_ID = " + self.CURRENT_BENCHMARK_ID + " | VOLTAGE_ID = " + self.CURRENT_VOLTAGE_ID + ")")

            
                if error_consecutive == self.RESET_AFTER_CONCECUTIVE_ERRORS:
                    self.logging.warning("Reseting DUT. Error_consecutive: " + str(error_consecutive))
                    self.reset_button()

                if error_consecutive >= (self.RESET_AFTER_CONCECUTIVE_ERRORS + 1):
                    self.logging.warning("Power Cycling DUT. Error_consecutive: " + str(error_consecutive))
                    self.power_cycle(True)

                self.save_state()

                if ((self.effective_total_elapsed_minutes > self.FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES) \
                    or ((self.reset_counter + self.power_cycle_counter) > self.FINISH_AFTER_TOTAL_ERRORS)):
                    break
                
            self.logging.info("Finished. Total elapsed: "+ experiment_elapsed_sec_str + \
                    " (BENCH_ID = " + self.CURRENT_BENCHMARK_ID + " | VOLTAGE_ID = " + self.CURRENT_VOLTAGE_ID + ")")
            
        except Exception:
            self.logging.warning(self.traceback.format_exc())
            pass
 
    def undervolt_characterization(self, benchmark:str, depth:int, run_times:int):
        undervolt_cmd = "sudo /home/eslab/undervolt/ZenStates-Linux/zenstates.py -p0 --vid {VID}"
        results = []
        first_exec = True

        self.logging.info("Starting undervolting characterization for " + benchmark + "...")
        for vid_offset in range(depth):
            # Adjust the voltage.
            results = self.remote_execute(undervolt_cmd.format(VID = str(0x21 + vid_offset)), self.VOLTAGE_CONFIG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1, 1)[0]
            self.sleep(5)
            if first_exec == True:
                first_exec = False
                self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_COLD_CACHE_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1, 1)
            else:
                # Run the benchmark
                self.dmesg_index += len(self.dmesg_diff)
                results = self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_COLD_CACHE_TIMEOUT * run_times, self.NETWORK_TIMEOUT_SEC, self.dmesg_index, run_times)
                self.dmesg_diff = results[len(results) - 1]["dmesg_diff"]

        # reset.
        self.sleep(3)
        self.remote_execute(undervolt_cmd.format(VID = str(0x21)), self.VOLTAGE_CONFIG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1, 1) 
        self.sleep(3)

def main():
    # Initialize Tester object
    test = Tester()
    test.get_setup_informations()
    voltage_list = test.get_voltage_list()
    benchmarks_list = test.get_benchmarks_list()

    # Set the thresholds for experiment termination
    finsh_after_effective_total_elapsed_minutes = 15 # minutes
    finish_after_total_errors = 100
    # For each voltage level and benchmark combination, set the benchmark and voltage ID,
    # set the experiment termination thresholds, and start the experiment

    for voltage_id in voltage_list:
        for benchmark_id in benchmarks_list:
            #test.debug_reset_disable()
            #test.debug_set_high_timeouts()
            test.set_benchmark_voltage_id(benchmark_id, voltage_id)
            test.set_finish_after_effective_minutes_or_total_errors(finsh_after_effective_total_elapsed_minutes, \
                finish_after_total_errors)
            test.experiment_start()
    
    test.enalbe_lower_frequency()
    test.get_setup_informations()
    voltage_list = test.get_voltage_list()
    benchmarks_list = test.get_benchmarks_list()
    for voltage_id in voltage_list:
        for benchmark_id in benchmarks_list:
            #test.debug_reset_disable()
            #test.debug_set_high_timeouts()
            test.set_benchmark_voltage_id(benchmark_id, voltage_id)
            test.set_finish_after_effective_minutes_or_total_errors(finsh_after_effective_total_elapsed_minutes, \
                finish_after_total_errors)
            test.experiment_start()

    # Benchmark charactarization  
    #for benchmark_id in benchmarks_list:
    #    test.set_benchmark_voltage_id(benchmark_id, voltage_list[0])
    #    test.undervolt_characterization(benchmark_id, 9, 15)

    #test.get_timeouts() # Uncomment this line to get the current timeouts
    #test.power_button() # Uncomment this line to press the power button
if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate") 
        proc = main()
    except Exception as exection:
            print(exection)  # If there's an exception, print it and continue
            pass
    except KeyboardInterrupt: # If the user presses Ctrl-C, exit the program
        print('Exiting program')
        sys.exit
        pass
