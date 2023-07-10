#!/usr/bin/env python
import sys # for exit
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
        
        regex = r'.*?PMD=(.*), SoC=(.*), DIMM1=(.*), DIMM2=(.*$)'
        self.power_regex = self.re.compile(regex, self.re.IGNORECASE)

        regex = r'.*?PMD:(.*)SoC:(.*$)'
        self.voltage_regex = self.re.compile(regex, self.re.IGNORECASE)

        regex = r'.*?PMD=(.*),.*?=(.*),.*?=(.*)'
        self.temp_regex = self.re.compile(regex, self.re.IGNORECASE)

        self.power_cycle_counter = 0
        self.reset_counter = 0

        self.run_counter = 0
        self.effective_total_elapsed_minutes = 0
        self.sdc_counter = 0 
        self.experiment_total_elapsed_sec = 0.0
        self.experiment_start_time = self.time()    

        self.first_boot = True
        self.dmesg_index =0
        self.dmesg_diff = ""

        # CONSTANTS
        # check https://github.com/gtcasl/hpc-benchmarks/blob/master/NPB3.3/NPB3.3-MPI/
        self.benchmarks_list = ["MG", "CG", "FT", "IS", "LU", "EP"]
        self.benchmark_commands = {
            "MG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/mg.A.8',
            "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/cg.A.8',
            "FT" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ft.A.8', 
            "IS" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/is.A.8',
            "LU" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/lu.A.8',
            "EP" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ep.A.8'
        }

        # Voltage Combinations for Beaming
        # PMD -  SOC
        # 980 - 950
        # 960 - 940
        # 940 - 930
        # 930 - 920

        # Non Safe Voltage
        # PMD -  SOC
        # 910 - 950
        self.voltage_list = ["V910", "V930", "V940", "V960", "V980"]
        self.voltage_commands = {
            "V980" : '/root/triumf/symphony/target/bash_scripts/voltset ALL 980',
            "V960" : '/root/triumf/symphony/target/bash_scripts/voltset ALL 960',
            "V940" : '/root/triumf/symphony/target/bash_scripts/voltset ALL 940', 
            "V930" : '/root/triumf/symphony/target/bash_scripts/voltset ALL 930',
            "V910" : '/root/triumf/symphony/target/bash_scripts/voltset PMD 910'  
        }

        #HDD
        self.timeouts = {
            "BOOT" : 80, 
            "MG" : 3,
            "CG" : 3,
            "FT" : 50, 
            "IS" : 2,
            "LU" : 28,
            "EP" : 6,
            "V980" : 11, 
            "V960" : 41,
            "V940" : 81,
            "V930" : 101,
            "V910" : 71
        }
     
        self.CURRENT_BENCHMARK_ID = "MG"
        self.CURRENT_VOLTAGE_ID = "V980"
        self.FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES = 100
        self.FINISH_AFTER_TOTAL_ERRORS = 100 
        self.TIMEOUT_SCALE_BENCHMARK = 2.0
        self.TIMEOUT_SCALE_BOOT = 1.1
        self.TIMEOUT_COLD_CACHE_SCALE_BENCHMARK = 4.0
        self.TIMEOUT_SCALE_VOLTAGE = 1.2
        self.RESET_AFTER_CONCECUTIVE_ERRORS = 2
        # The DUT power cycles after (RESET_AFTER_CONCECUTIVE_ERRORS + 1)
        
        # Measurements with LU / V910
        self.CURRENT_PMD_THRESHOLD = 16.5 #15.28 
        self.CURRENT_SOC_THRESHOLD = 8.50 #7.97
        self.POWER_DIMM1_THRESHOLD = 9.0 #6.745
        self.TEMP_PMD_THRESHOLD = 75 #63
        self.TEMP_SOC_THRESHOLD = 75 #60 
        self.TEMP_DIMM1_THRESHOLD = 75 #64

        self.CURRENT_PMD_THRESHOLD_SCALE = 1.02
        self.CURRENT_SOC_THRESHOLD_SCALE = 1.02
        self.POWER_DIMM1_THRESHOLD_SCALE = 1.02
        self.TEMP_PMD_THRESHOLD_SCALE = 1.1
        self.TEMP_SOC_THRESHOLD_SCALE = 1.1
        self.TEMP_DIMM1_THRESHOLD_SCALE = 1.1

        self.current_pmd_threshold_max = 0 
        self.current_soc_threshold_max = 0 
        self.temp_pmd_threshold_max = 0 
        self.temp_soc_threshold_max = 0 
        self.temp_dimm1_threshold_max = 0
        self.power_dimm1_threshold_max = 0

        self.EXECUTION_ATTEMPT = 1
        self.NETWORK_TIMEOUT_SEC = 2

        
        self.TARGET_IP = "10.30.0.100" #"localhost"
        self.TARGET_PORT = 18861 

        self.GPIO_HOST_IP = "10.30.0.63"
        self.GPIO_HOST_PORT = 18861
        
        #DEBUG
        self.DISABLE_RESET = False
        self.SAVE_THRESHOLDS = False

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
        self.temp_soc_threshold_max = 0 
        self.temp_dimm1_threshold_max = 0
        self.power_dimm1_threshold_max = 0

        self.power_cycle_counter = 0
        self.reset_counter = 0

        self.run_counter = 0
        self.effective_total_elapsed_minutes = 0
        self.sdc_counter = 0 
        self.experiment_total_elapsed_sec = 0.0
        self.experiment_start_time = self.time()    

        self.restore_thresholds()    

    def set_benchmark_voltage_id(self, id_str, voltage_id_str):
        self.logging.warning("Setting CURRENT_BENCHMARK_ID = " + id_str)
        self.CURRENT_BENCHMARK_ID = id_str
        self.logging.warning("Setting CURRENT_VOLTAGE_ID = " + voltage_id_str)
        self.CURRENT_VOLTAGE_ID = voltage_id_str
        self._update()

    def set_finish_after_effective_minutes_or_total_errors(self, finish_after_effective_min, finish_after_total_errors):
            self.logging.warning("Setting RUNS_PER_TEST = " + str(finish_after_effective_min))
            self.FINISH_AFTER_TOTAL_EFFECTIVE_MINUTES = finish_after_effective_min
            self.FINISH_AFTER_TOTAL_ERRORS = finish_after_total_errors
            
    
    def debug_reset_disable(self):
        self.DISABLE_RESET = True


    def debug_set_high_timeouts(self):
        self.timeouts = {
            "BOOT" : 300, 
            "MG" : 300,
            "CG" : 300,
            "FT" : 300, 
            "IS" : 300,
            "LU" : 300,
            "EP" : 300,
            "V980" : 300, 
            "V960" : 300,
            "V940" : 300,
            "V930" : 300,
            "V910" : 300
        }
        self.logging.warning("debug_set_high_timeouts")

    def press_button(self, relay, hold_time):
        try:
            client = GPIOClient(self.GPIO_HOST_IP, self.GPIO_HOST_PORT)
            client.connect()
            client.turn_on(relay)
            self.sleep(hold_time)
            client.turn_off(relay)
            client.disconnect()
        except Exception as e:
            self.logging.warning(e)

    def power_cycle(self, count_enable):
        """
        Power cycle the TARGET BOARD, and optionally increment the power cycle counter.
        Args:
            count_enable (bool): Whether to increment the power cycle counter.
        """
        self.first_boot = True
        self.dmesg_diff = 1

        self.press_button(self.POWER_RELAY_ID, 0.25)
        self.sleep(1)
        self.press_button(self.POWER_RELAY_ID, 0.25)

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

        self.press_button(self.POWER_RELAY_ID, 0.25)

    def reset_button(self):
        """
        Simulate pressing the reset button on the TARGET BOARD, 
        and increment the reset counter.
        """
        self.first_boot = True
        self.dmesg_index = 1

        self.press_button(self.RESET_RELAY_ID, 0.25)

        self.reset_counter +=1
        self.logging.warning('Reset')
        if self.remote_alive(self.BOOT_TIMEOUT_SEC):
            self.logging.info("Booted")
            self.set_voltage()
            
    def get_dmesg(self):
        run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg = \
            self.remote_execute("date", self.DMESG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1) 
        return dmesg

    def set_voltage(self):
        self.logging.info('Configuring voltage: ' + self.COMMAND_VOLTAGE)
        healthlog, run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = \
            self.remote_execute(self.COMMAND_VOLTAGE, self.VOLTAGE_CONFIG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1) 
        if return_code != '0':
            self.logging.warning('Return error code: ' + return_code + ' Configuring voltage: ' + self.COMMAND_VOLTAGE)

    def remote_alive(self, boot_timeout_sec: int):
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
        
    def remote_execute(self, command:str, command_timeout_sec:int, network_timout_sec: int, dmesg_index:int):
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
                        healthlog, run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = c.root.execute(command, dmesg_index)
                        time = str(self.math.ceil(self.timeit.default_timer() - start))
                        self.logging.info("Remote_execute(" + command + ") elapsed (seconds): " + time)

                        if return_code != '0':
                            self.logging.error("ERROR WHEN RUNNING: " + run_command + " STDERR: " + stderror)
                        c.close() 
                        return healthlog, run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff  
                    except:
                        c.close()
                        if  execution_attempt_counter > self.EXECUTION_ATTEMPT:
                            self.reset_button()
                        else:
                            self.logging.warning("Execution timeout. Attempt " + str(execution_attempt_counter))
                        execution_attempt_counter += 1
                        
            except:
                conn_count_thresh -= 1 
                attemp_counter += 1
                self.logging.warning('Remote is down..trying to connect. Attempt: ' + str(attemp_counter))
                self.sleep(sleep_sec_excep)
                if conn_count_thresh <=0:
                    self.reset_button()
                    conn_count_thresh =  int(network_timout_sec / sleep_sec_excep)
   
    def save_result(self, healthlog, run_counter, run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff, correct):
        now = self.datetime.now() # current date and time
        result_date = now.strftime("%m_%d_%Y__%H_%M_%S")
        result_file_name = 'results/' + self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_" + result_date + '.json'
        result = {
                    "timestamp" : timestamp,
                    "run_command": run_command,
                    "return_code" : return_code,
                    "run_counter" : run_counter, 
                    "correct" : correct,
                    "duration_ms" : duration_ms,
                    "power" : power,
                    "temp" : temp,
                    "voltage" : voltage,
                    "freq" : freq,
                    "stdoutput" : stdoutput,
                    "stderror" : stderror,
                    "dmesg_diff" : dmesg_diff,
                    "healthlog" : healthlog,
                    "dmesg_index" : str(self.dmesg_index)
        }
        with open(result_file_name, "w") as json_file:
            self.json.dump(result, json_file)
            
    def save_state(self):
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
        except Exception:
            self.logging.error(self.traceback.format_exc())
            pass

    def restore_state(self):
        filename = self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_state.json"
        state_file = "./state/" + filename
        try:
            with open(state_file, 'r') as json_file:
                state =self.json.load(json_file)
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

        filename = self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_thresholds.json"
        threshold_file = "./config/" + filename

        threshold = {
            "current_pmd_threshold_max": str(self.current_pmd_threshold_max),
            "current_soc_threshold_max" : str(self.current_soc_threshold_max) ,
            "power_dimm1_threshold_max" : str(self.power_dimm1_threshold_max), 
            "temp_pmd_threshold_max" : str(self.temp_pmd_threshold_max),
            "temp_soc_threshold_max" : str(self.temp_soc_threshold_max),
            "temp_dimm1_threshold_max" : str(self.temp_dimm1_threshold_max)   
        }
        try:
            with open(threshold_file, "w") as json_file:
                self.json.dump(threshold, json_file)
        except Exception:
            self.logging.error(self.traceback.format_exc())
            pass
    
    def restore_thresholds(self):
        filename = self.CURRENT_BENCHMARK_ID + "_" + self.CURRENT_VOLTAGE_ID + "_thresholds.json"
        threshold_file = "./config/" + filename
        try:
            with open(threshold_file, 'r') as json_file:
                threshold =self.json.load(json_file)
                self.CURRENT_PMD_THRESHOLD = float(threshold["current_pmd_threshold_max"]) * self.CURRENT_PMD_THRESHOLD_SCALE
                self.CURRENT_SOC_THRESHOLD = float(threshold["current_soc_threshold_max"]) * self.CURRENT_SOC_THRESHOLD_SCALE
                self.POWER_DIMM1_THRESHOLD = float(threshold["power_dimm1_threshold_max"]) * self.POWER_DIMM1_THRESHOLD_SCALE
                self.TEMP_PMD_THRESHOLD = self.math.ceil(int(threshold["temp_pmd_threshold_max"]) * self.TEMP_PMD_THRESHOLD_SCALE)
                self.TEMP_SOC_THRESHOLD = self.math.ceil(int(threshold["temp_soc_threshold_max"]) * self.TEMP_SOC_THRESHOLD_SCALE)
                self.TEMP_DIMM1_THRESHOLD = self.math.ceil(int(threshold["temp_dimm1_threshold_max"]) * self.TEMP_DIMM1_THRESHOLD_SCALE)
                
                self.logging.warning("Setting CURRENT_PMD_THRESHOLD = " + str(self.CURRENT_PMD_THRESHOLD))
                self.logging.warning("Setting CURRENT_SOC_THRESHOLD = " + str(self.CURRENT_SOC_THRESHOLD))
                self.logging.warning("Setting POWER_DIMM1_THRESHOLD = " + str(self.POWER_DIMM1_THRESHOLD))
                self.logging.warning("Setting TEMP_PMD_THRESHOLD = " + str(self.TEMP_PMD_THRESHOLD))
                self.logging.warning("Setting TEMP_SOC_THRESHOLD = " + str(self.TEMP_SOC_THRESHOLD))
                self.logging.warning("Setting TEMP_DIMM1_THRESHOLD = " + str(self.TEMP_DIMM1_THRESHOLD))
        except Exception:
            self.logging.warning(threshold_file + " file not found") 
            pass

    def is_result_correct(self, result):
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
            self.logging.error(self.traceback.format_exc())
            return False
    
    
    def get_timeouts(self):

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

            # Voltage Combinations for Beaming
            # PMD -  SOC
            # 980 - 950
            # 960 - 940
            # 940 - 930
            # 930 - 920

            # Non Safe Voltage
            # PMD -  SOC
            # 910 - 950
            self.COMMAND_VOLTAGE = "/root/triumf/symphony/target/bash_scripts/voltset ALL 980" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time 980: " + voltage_config_time)

            self.COMMAND_VOLTAGE = "/root/triumf/symphony/target/bash_scripts/voltset ALL 960" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time 960: " + voltage_config_time)

            self.COMMAND_VOLTAGE = "/root/triumf/symphony/target/bash_scripts/voltset ALL 940" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time 940: " + voltage_config_time)

            self.COMMAND_VOLTAGE = "/root/triumf/symphony/target/bash_scripts/voltset ALL 930" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time 930: " + voltage_config_time)

            start = self.timeit.default_timer()
            self.remote_execute(self.BENCHMARK_COMMAND, 100, self.NETWORK_TIMEOUT_SEC, 1)
            time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("benchmark_time 930 " + self.CURRENT_BENCHMARK_ID + ":" + time)

            for item in self.benchmarks_list:
                self.CURRENT_BENCHMARK_ID = item
                self.BENCHMARK_COMMAND = self.benchmark_commands[self.CURRENT_BENCHMARK_ID]
                start = self.timeit.default_timer()
                self.remote_execute(self.BENCHMARK_COMMAND, 100, self.NETWORK_TIMEOUT_SEC, 1)
                time = str(self.math.ceil(self.timeit.default_timer() - start))
                self.logging.info("benchmark_time 930 " + self.CURRENT_BENCHMARK_ID + ":" + time)

            self.COMMAND_VOLTAGE = "/root/triumf/symphony/target/bash_scripts/voltset ALL 910" 
            start = self.timeit.default_timer()
            self.set_voltage()
            voltage_config_time = str(self.math.ceil(self.timeit.default_timer() - start))
            self.logging.info("voltage_config_time 910: " + voltage_config_time)

        except Exception:
            self.logging.warning(self.traceback.format_exc())
            pass

    def parse_monitor_data(self,power, voltage, temp):
        try:
            power_str = self.power_regex.findall(power)
            power_pmd = float(power_str[0][0])
            power_soc = float(power_str[0][1])
            power_dimm1 = float(power_str[0][2])
            power_dimm2 = float(power_str[0][3])


            voltage = str(voltage).replace("\n","")
            voltage_str = self.voltage_regex.findall(voltage)
            voltage_pmd = round((float(voltage_str[0][0])/1000),3)
            voltage_soc = round((float(voltage_str[0][1])/1000),3)
            current_pmd = round((power_pmd / (voltage_pmd)),2)
            current_soc = round((power_soc / (voltage_soc)),2)

            temp_str = self.temp_regex.findall(temp)
            temp_pmd = int(temp_str[0][0])
            temp_soc = int(temp_str[0][1])
            temp_dimm = int(temp_str[0][2])
    
            power_curr_volt_temp_str = "MONITOR: PMD = "+ str(power_pmd) + "(W)/" + str(current_pmd) + "(A)/" + str(voltage_pmd) +"(V)/" \
                + str(temp_pmd)+"(C) | SoC = "+ str(power_soc) + "(W)/" + str(current_soc) + "(A)/" + str(voltage_soc) +"(V)/" + str(temp_soc)+"(C)" \
                    + " | DIMM1 = "+ str(power_dimm1) + "(W)/" + str(temp_dimm)+"(C)"
            self.logging.info(power_curr_volt_temp_str)
            
            if current_pmd > self.current_pmd_threshold_max:
                self.current_pmd_threshold_max = current_pmd
            if current_soc > self.current_soc_threshold_max:
                self.current_soc_threshold_max = current_soc
            if power_dimm1 > self.power_dimm1_threshold_max:
                self.power_dimm1_threshold_max = power_dimm1
            if temp_pmd > self.temp_pmd_threshold_max:
                self.temp_pmd_threshold_max = temp_pmd
            if temp_soc > self.temp_soc_threshold_max:
                self.temp_soc_threshold_max = temp_soc
            if temp_dimm > self.temp_dimm1_threshold_max:
                self.temp_dimm1_threshold_max = temp_dimm

            if self.SAVE_THRESHOLDS == True:
                self.save_thresholds()

            max_power_curr_volt_temp_str = "MONITOR(MAX): PMD = " + str(self.current_pmd_threshold_max) + "(A)/" + str(voltage_pmd) +"(V)/" \
                + str(self.temp_pmd_threshold_max)+"(C) | SoC = " + str(self.current_soc_threshold_max) + "(A)/" + str(self.temp_soc_threshold_max)+"(C)" \
                    + " | DIMM1 = "+ str(self.power_dimm1_threshold_max) + "(W)/" + str(self.temp_dimm1_threshold_max)+"(C)"
            
            self.logging.info(max_power_curr_volt_temp_str)

            if current_pmd > self.CURRENT_PMD_THRESHOLD:
                self.logging.critical("PMD overcurrent: " + str(current_pmd) + "(A)")
            if current_soc > self.CURRENT_SOC_THRESHOLD:
                self.logging.critical("SOC overcurrent: " + str(current_soc) + "(A)")
            if power_dimm1 > self.POWER_DIMM1_THRESHOLD:
                self.logging.critical("DIMM1 overpower: " + str(power_dimm1) + "(W)")
            if temp_pmd > self.TEMP_PMD_THRESHOLD:
                self.logging.critical("PMD over temperature: " + str(temp_pmd) + "(C)")
            if temp_soc > self.TEMP_SOC_THRESHOLD:
                self.logging.critical("SOC over temperature: " + str(temp_soc) + "(C)")
            if temp_dimm > self.TEMP_DIMM1_THRESHOLD:
                self.logging.critical("DIMM1 over temperature: " + str(temp_dimm) + "(C)")

        except Exception:
            self.logging.warning(self.traceback.format_exc())
            pass
    
    def experiment_start(self):
        experiment_elapsed_sec_str = ""
        self.logging.info('Starting... Benchmark: ' + self.BENCHMARK_COMMAND)
        
        self.power_cycle(False)
        
        error_consecutive = 0

        self.restore_state()

        try:
            while True:
                #command:str, command_timeout_sec:int, network_timout_sec: int, dmesg_index:int)
                
                if self.first_boot == True:
                    self.first_boot = False
                    healthlog, run_command, timestamp, power, temp, voltage, freq, effective_run_elapsed_ms, stdoutput, stderror, return_code, dmesg_diff = \
                    self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_COLD_CACHE_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1)
                    self.dmesg_diff = dmesg_diff
                else:
                    self.dmesg_index += len(self.dmesg_diff)    
                    healthlog, run_command, timestamp, power, temp, voltage, freq, effective_run_elapsed_ms, stdoutput, stderror, return_code, dmesg_diff = \
                        self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_TIMEOUT, self.NETWORK_TIMEOUT_SEC, self.dmesg_index)
                    self.dmesg_diff = dmesg_diff
                   
                self.run_counter += 1
                self.effective_total_elapsed_minutes += (float(effective_run_elapsed_ms)/1000)/60
                effective_elapsed_min = str("{:.2f}".format(round(self.effective_total_elapsed_minutes, 2)))
                correct = self.is_result_correct(stdoutput)
                self.save_result(healthlog, str(self.run_counter), run_command, timestamp, power, temp, voltage, freq, effective_run_elapsed_ms, stdoutput, stderror, return_code, dmesg_diff, str(correct))
                if correct == False:
                    self.logging.error("Result SDC detected")
                    self.logging.error("Error_consecutive: " + str(error_consecutive))
                    error_consecutive += 1
                    self.sdc_counter += 1

                else: 
                    error_consecutive = 0
                
                
                log_str = "Run: " + str(self.run_counter) + " | Correct: " + str(correct) + " | Effect-run-elapsed(ms): " + effective_run_elapsed_ms \
                    + " | timestamp: " + timestamp            
                self.logging.info(log_str)

                
                log_str = "Resets: " + str(self.reset_counter) + " | PowerCycles: " + str(self.power_cycle_counter) \
                    + " | Effective-elapsed(min): " + str(effective_elapsed_min) +  " | SDCs: " +  str(self.sdc_counter)
                self.logging.info(log_str)

                self.experiment_total_elapsed_sec = (self.time() - self.experiment_start_time)
                experiment_elapsed_sec_str = str(self.timedelta(seconds=self.experiment_total_elapsed_sec))
                self.logging.info("Total elapsed: "+ experiment_elapsed_sec_str + \
                    " (BENCH_ID = " + self.CURRENT_BENCHMARK_ID + " | VOLTAGE_ID = " + self.CURRENT_VOLTAGE_ID + ")")

                self.parse_monitor_data(power, voltage, temp)
            
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
    
def main():
    test = Tester()
    voltage_list = ["V930", "V940","V960","V980"]
    benchmarks_list = ["MG", "LU", "EP", "FT", "IS", "CG"]
    finsh_after_effective_total_elapsed_minutes = 90 # minutes
    finish_after_total_errors = 100
    for voltage_id in voltage_list:
        for benchmark_id in benchmarks_list:
            #test.debug_reset_disable()
            #test.debug_set_high_timeouts()
            test.set_benchmark_voltage_id(benchmark_id, voltage_id)
            test.set_finish_after_effective_minutes_or_total_errors(finsh_after_effective_total_elapsed_minutes, \
                finish_after_total_errors)
            test.experiment_start()
    #test.get_timeouts()
    #test.power_button()
if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate") 
        proc = main()
    except Exception as exection:
            print(exection)
            pass
    except KeyboardInterrupt:
        print('Exiting program')
        sys.exit
        pass