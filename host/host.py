#!/usr/bin/env python
import sys # for exit


class Tester:
    import rpyc
    from time import sleep
    import serial
    from serial.tools import list_ports #pyserial, esptool
    import json
    import re
    from datetime import datetime
    import logging


    def __init__(self):
        #Global variables
        self.now = self.datetime.now() # current date and time
        self.log_date = self.now.strftime("%m_%d_%Y__%H_%M_%S")
        self.log_file_name = 'logs/log_' + self.log_date + '.log'
        self.logging.basicConfig(filename=self.log_file_name, encoding='utf-8', format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s' \
            ,level=self.logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
        formatter = self.logging.Formatter(fmt='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                              datefmt='%Y-%m-%d,%H:%M:%S')
        screen_handler = self.logging.StreamHandler()
        screen_handler.setFormatter(formatter)
        self.logging.getLogger().addHandler(screen_handler)


        self.regex = r'Verification( +)=( +)(SUCCESSFUL)'
        self.success_regex = self.re.compile(self.regex, self.re.IGNORECASE)

        self.first_dmesg = True

        self.power_cycle_counter = 0
        self.reset_counter = 0

        self.run_counter = 0
        self.duration_min_total = 0
        self.sdc_counter = 0     

        # CONSTANTS
        self.benchmarks_list = ["MG", "CG", "CG", "IS", "LU", "EP"]
        self.benchmark_commands = {
            "MG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/mg.A.8',
            "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/cg.A.8',
            "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ft.A.8', 
            "IS" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/is.A.8',
            "LU" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/lu.A.8',
            "EP" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ep.A.8'
        }

        self.TARGET_IP = "10.30.0.100" #"localhost"
        self.TARGET_PORT = 18861
        self.BOOT_TIMEOUT_SEC = 150
        self.POWER_CYCLE_ATTEMPS = 5
        self.NETWORK_TIMEOUT_SEC = 5
        self.BENCHMARK_TIMEOUT = 1
        self.BENCHMARK_COLD_CACHE_TIMEOUT = 20
        self.DMESG_TIMEOUT = 100
        self.VOLTAGE_CONFIG_TIMEOUT = 150
        self.CURRENT_BENCHMARK_ID = "MG"
        self.BENCHMARK_COMMAND = self.benchmark_commands[self.CURRENT_BENCHMARK_ID]
        self.EXECUTION_ATTEMPT = 3
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
        #self.COMMAND_VOLTAGE = "/root/triumf/symphony/target/bash_scripts/voltset PMD 910" 

    def find_reset_uart(self, VID:str, PID:str, SERIAL_NUM:str):
        """This function finds the specific UART that is used for resetting and power cycling the XGENE-2

        Args:
            VID (str): USB2UART Vendor ID
            PID (str): USB2UART Product ID
            SERIAL_NUM (str): Self explained

        Returns:
            serial.Serial(): Returns the uart driver
        """    
        port = None
        device_list = self.list_ports.comports()
        for device in device_list:
            if (device.vid != None or device.pid != None or device.serial_number != None):
                if ('{:04X}'.format(device.vid) == VID and
                    '{:04X}'.format(device.pid) == PID and
                    device.serial_number == SERIAL_NUM):
                    port = device.device
                    break        
    
        BAUDRATE = '19200'
        ser = self.serial.Serial()
        ser.baudrate = BAUDRATE
        try:
            ser.port = port
            ser.dtr = False
            ser.rts = False
            ser.open()
            ser.dtr = False
            ser.rts = False
            self.logging.info("Opening serial port:" + port + " @" + BAUDRATE)
            return ser
        except:
            if port == None:
                self.logging.critical("Cannot find reset UART")
            # while True:
            #     dummy = None
            
    
    

    def power_button(self, count_enable):
        VID = '0403'
        PID = '6001'
        SERIAL_NUM = 'A50285BI'
        ser = self.find_reset_uart(VID, PID, SERIAL_NUM)
        if ser != None:
            ser.dtr = True
            self.sleep(2)
            ser.dtr = False
            self.sleep(2)
            ser.dtr = True
            self.sleep(2)
            ser.dtr = False
            ser.close()

        if count_enable == True:
            self.power_cycle_counter += 1
        self.logging.warning("Power Cycle")
        if self.remote_alive(self.BOOT_TIMEOUT_SEC):
            run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = \
                self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_COLD_CACHE_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1)
            self.set_voltage()


    def reset_button(self):
        VID = '0403'
        PID = '6001'
        SERIAL_NUM = 'A50285BI'
        ser = self.find_reset_uart(VID, PID, SERIAL_NUM)
        if ser != None:
            ser.rts = True
            self.sleep(1)
            ser.rts = False
            ser.close()
        self.reset_counter +=1
        self.logging.warning('Reset')
        if self.remote_alive(self.BOOT_TIMEOUT_SEC):
            run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = \
                self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_COLD_CACHE_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1)
            self.set_voltage()


    def get_dmesg(self):
        run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg = \
            self.remote_execute("date", self.DMESG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1) 
        return dmesg

    def set_voltage(self):     
        run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = \
            self.remote_execute(self.COMMAND_VOLTAGE, self.VOLTAGE_CONFIG_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1)
        self.logging.info('Configuring voltage: ' + self.COMMAND_VOLTAGE)
        if return_code != '0':
            self.logging.critical('Return error code: ' + return_code + ' Configuring voltage: ' + self.COMMAND_VOLTAGE)

    def remote_alive(self, boot_timeout_sec: int):
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
                        return alive 
                    except:
                        c.close()   
            except:
                conn_count_thresh -= 1 
                attemp_counter += 1
                self.logging.critical('Remote is down..trying to connect. Attemp: ' + str(attemp_counter))
                self.sleep(sleep_sec_excep)
                if conn_count_thresh <=0:
                    self.power_button(True)
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
                        run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = c.root.execute(command, dmesg_index)
                        if return_code != '0':
                            self.logging.error("ERROR WHEN RUNNING: " + run_command + " STDERR: " + stderror)
                        c.close() 
                        return run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff  
                    except:
                        c.close()
                        if  execution_attempt_counter > self.EXECUTION_ATTEMPT:
                            self.reset_button()
                        else:
                            self.logging.critical("Execution timeout. Attempt " + str(execution_attempt_counter))
                        execution_attempt_counter += 1
                        
            except:
                conn_count_thresh -= 1 
                attemp_counter += 1
                self.logging.critical('Remote is down..trying to connect. Attemp: ' + str(attemp_counter))
                self.sleep(sleep_sec_excep)
                if conn_count_thresh <=0:
                    self.reset_button()
                    conn_count_thresh =  int(network_timout_sec / sleep_sec_excep)

    def save_result(self, run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff, correct):
        now = self.datetime.now() # current date and time
        result_date = now.strftime("%m_%d_%Y__%H_%M_%S")
        result_file_name = 'results/result_' + result_date + '.json'
        result = {
                    "timestamp" : timestamp,
                    "run_command": run_command,
                    "return_code" : return_code,
                    "correct" : correct,
                    "duration_ms" : duration_ms,
                    "power" : power,
                    "temp" : temp,
                    "voltage" : voltage,
                    "freq" : freq,
                    "stdoutput" : stdoutput,
                    "stderror" : stderror,
                    "dmesg_diff" : dmesg_diff
        }
        with open(result_file_name, "w") as json_file:
            self.json.dump(result, json_file)


    def is_result_correct(self, result):
        success_str = self.success_regex.findall(result)
        if success_str[0][2] == "SUCCESSFUL":
            return True
        else:
            return False

    def experiment_start(self):

        self.logging.info('Starting... Benchmark: ' + self.BENCHMARK_COMMAND)
        
        self.power_button(False)
        
        error_consecutive = 0

        while True:
            #command:str, command_timeout_sec:int, network_timout_sec: int, dmesg_index:int)
            run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = \
                self.remote_execute(self.BENCHMARK_COMMAND, self.BENCHMARK_TIMEOUT, self.NETWORK_TIMEOUT_SEC, 1)
            self.run_counter += 1
            self.duration_min_total += (float(duration_ms)/1000)/60
            duration_min_total_str = str("{:.2f}".format(round(self.duration_min_total, 2)))
            correct = self.is_result_correct(stdoutput)
            self.save_result(run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff, str(correct))
            if correct == False:
                self.logging.error("Result SDC detected")
                self.logging.error("Error_consecutive: " + error_consecutive)
                error_consecutive += 1
                self.sdc_counter += 1

            else: 
                error_consecutive = 0
                log_str = timestamp + " | run_counter: " + str(self.run_counter) + " | Correct: " + str(correct) + " | Duration_ms: " + duration_ms        
                self.logging.info(log_str)

            log_str = "run_counter: " + str(self.run_counter) + " | Resets: " + str(self.reset_counter) + " | PowerCycles: " + str(self.power_cycle_counter)  \
                + " | Total_minutes: " + str(duration_min_total_str) +  " | SDCs: " +  str(self.sdc_counter)
            self.logging.info(log_str)

            if error_consecutive == 2:
                self.reset_button()

            if error_consecutive == 3:
                self.power_button(True)

def main():
    test = Tester()
    test.experiment_start()

if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate") 
        proc = main()
    except KeyboardInterrupt:
        print('Exiting program')
        sys.exit
        pass