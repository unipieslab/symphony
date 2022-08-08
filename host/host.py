
#!/usr/bin/env python
import sys # for exit
import rpyc
from time import sleep
import serial
from serial.tools import list_ports #pyserial, esptool
import json
import re

#Global variables
command_timeout_counter = 0
connection_timeout_counter = 0
sdc_counter = 0
reset_counter = 0
power_cycle_counter = 0

regex = r'Verification( +)=( +)(SUCCESSFUL)'
success_regex = re.compile(regex, re.IGNORECASE)

first_dmesg = True

# CONSTANTS
TARGET_IP = "10.30.0.100" #"localhost"
TARGET_PORT = 18861
BOOT_TIMEOUT_SEC = 150
BOOT_BENCHMARK_TIMOUT_SEC = 20

# Voltage Combinations for Beaming
# PMD -  SOC
# 980 - 950
# 960 - 940
# 940 - 930
# 930 - 920

COMMAND_VOLTAGE = "/root/triumf/symphony/target/bash_scripts/voltset ALL 980" 

CURRENT_BENCHMARK_ID = "MG"
benchmarks_list = ["MG", "CG", "CG", "IS", "LU", "EP"]
benchmark_commands = {
    "MG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/mg.A.8',
    "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/cg.A.8',
    "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ft.A.8', 
    "IS" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/is.A.8',
    "LU" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/lu.A.8',
    "EP" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ep.A.8'
}


def find_reset_uart(VID:str, PID:str, SERIAL_NUM:str):
    """This function finds the specific UART that is used for resetting and power cycling the XGENE-2

    Args:
        VID (str): USB2UART Vendor ID
        PID (str): USB2UART Product ID
        SERIAL_NUM (str): Self explained

    Returns:
        serial.Serial(): Returns the uart driver
    """    
    port = None
    device_list = list_ports.comports()
    for device in device_list:
        if (device.vid != None or device.pid != None or device.serial_number != None):
            if ('{:04X}'.format(device.vid) == VID and
                '{:04X}'.format(device.pid) == PID and
                device.serial_number == SERIAL_NUM):
                port = device.device
                break        
   
    BAUDRATE = '19200'
    ser = serial.Serial()
    ser.baudrate = BAUDRATE
    try:
        ser.port = port
        ser.dtr = False
        ser.rts = False
        ser.open()
        print("opening serial port:" + port + " @" + BAUDRATE)
        print("--------------------------------")
        return ser
    except:
        if port == None:
            print("--------------------------------")
            print("ALERT: CANNOT FIND UART FOR RESET")
            print("--------------------------------")
            while True:
                pass
    
VID = '0403'
PID = '6001'
SERIAL_NUM = 'A50285BI'
ser = find_reset_uart(VID, PID, SERIAL_NUM)

def power_button():
    ser.dtr = True
    sleep(2)
    ser.dtr = False
    ser.dtr = True
    sleep(2)
    ser.dtr = False
    print("ACTION:POWER_CYCLE")
    if remote_alive(BOOT_TIMEOUT_SEC):
        set_voltage()


def reset_button():
    ser.rts = True
    sleep(1)
    ser.rts = False
    print("ACTION:RESET")
    if remote_alive(BOOT_TIMEOUT_SEC):
        set_voltage()

def get_dmesg():
    run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg = remote_execute("date", 150, 5, 1) 
    return dmesg

def set_voltage():     
    run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = remote_execute(COMMAND_VOLTAGE, 150, 5, 1)

def remote_alive(timeout_sec):
    alive = False
    while True:
        try:
            c = rpyc.connect(TARGET_IP, TARGET_PORT)
            c._config['sync_request_timeout'] = timeout_sec
            if not c.closed:
                print("connected to server")
                try:
                    alive = c.root.alive()
                    c.close()  
                    return alive 
                except:
                    c.close()   
        except:
            print("ERROR:REMOTE IS DOWN")
            sleep(0.5)
            pass
    
def remote_execute(command:str, command_timeout_sec:int, network_timout_sec: int, dmesg_index:int):
    sleep_sec_excep = 0.5 
    conn_count_thresh =  int(network_timout_sec / sleep_sec_excep)
    while True:
        try:
            c = rpyc.connect(TARGET_IP, TARGET_PORT)
            c._config['sync_request_timeout'] = command_timeout_sec
            if not c.closed:
                print("connected to server")
                try:
                    run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff = c.root.execute(command, dmesg_index)
                    if return_code != '0':
                        print("ERROR: WHEN RUNNING: " + run_command + " STDERR: " + stderror)
                    c.close() 
                    return run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff  
                except:
                    print("ERROR: EXECUTION TIMEOUT")
                    c.close() 
                    reset_button()
        except:
            conn_count_thresh =  conn_count_thresh - 1
            print("ERROR: CONNECTION TIMEOUT: " + str(conn_count_thresh))
            sleep(0.5)
            if conn_count_thresh <=0:
                reset_button()
                conn_count_thresh =  int(network_timout_sec / sleep_sec_excep)

def generate_golden():
    for id in benchmarks_list:
            command = benchmark_commands[id]
            run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff= remote_execute(command, 100, 1)
            print(stdoutput)
            info = {
                "command": run_command,
                "golden" : stdoutput,
                "execution_time" : duration_ms
            }
            json_path = "golden/" + id + ".json"
            with open(json_path, "w") as outfile:
                json.dump(info, outfile)

def is_result_correct(result):
    success_str = success_regex.findall(result)
    if success_str[0][2] == "SUCCESSFUL":
        return True
    else:
        return False

def main():
    #reset_button()
    command = benchmark_commands[CURRENT_BENCHMARK_ID]
    while True:
        run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff= remote_execute(command, 100, 5, 1)
        if is_result_correct(stdoutput):
            print("correct result")
    
                          
if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")   
        proc = main()
    except KeyboardInterrupt:
        print('Exiting program')
        sys.exit
        pass