
#!/usr/bin/env python
import sys # for exit
import rpyc
from time import sleep
import serial
from serial.tools import list_ports #pyserial, esptool
import json

#Global variables
command_timeout_counter = 0
connection_timeout_counter = 0
sdc_counter = 0
reset_counter = 0
power_cycle_counter = 0

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
#ser = find_reset_uart(VID, PID, SERIAL_NUM)

def power_button():
    # ser.dtr = True
    # sleep(2)
    # ser.dtr = False
    # ser.dtr = True
    # sleep(2)
    # ser.dtr = False
    print("ACTION:POWER_CYCLE")


def reset_button():
    # ser.rts = True
    # sleep(1)
    # ser.rts = False

    print("ACTION:RESET")

def get_empty_dict():
    run_dict = {
        'RUN_COMMAND' : '',
        'TIMESTAMP' : '',
        'STDOUT' : '', 
        'STDERROR': '',
        'RETURNCODE': '',
        'DMESG': '',
        'DURATION_MS': ''
    }
    return run_dict

def remote_execute(command:str, command_timeout_sec:int):
    try_reconn_sec = 5
    sleep_sec_excep = 0.5 
    conn_count_thresh =  int(try_reconn_sec / sleep_sec_excep)
    target_ip = "10.30.0.100" #"localhost"
    run_dict = get_empty_dict()
    try:
        c = rpyc.connect(target_ip, 18861)
        c._config['sync_request_timeout'] = command_timeout_sec
        if not c.closed:
            try:
                run_dict = c.root.execute(command)      
            except:
                print("ERROR:RUN_TIMEOUT")
                c.close() 
                reset_button()
        c.close()    
    except:
        conn_count_thresh =  conn_count_thresh - 1
        print("connection_error_counter_thresh: " + str(conn_count_thresh))
        sleep(0.5)
        if conn_count_thresh <=0:
            reset_button()
            conn_count_thresh =  int(try_reconn_sec / sleep_sec_excep)
    return run_dict

def generate_golden():
    benchmarks_list = ["MG", "CG", "CG", "IS", "LU", "EP"]
    benchmark_commands = {
        "MG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/mg.A.8',
        "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/cg.A.8',
        "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ft.A.8', 
        "IS" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/is.A.8',
        "LU" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/lu.A.8',
        "EP" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ep.A.8'
    }

    # for id in benchmarks_list:
    #         command = benchmark_commands[id]
    #         run_dict = remote_execute(command, 100)
    #         golden_info = run_dict['STDOUT']
    #         execution_time_info = run_dict['DURATION_MS']
    #         info = {
    #             "command": command,
    #             "golden" : golden_info,
    #             "execution_time" : execution_time_info
    #         }
    #         json_path = "golden/" + id + ".json"
    #         with open(json_path, "w") as outfile:
    #             json.dump(info, outfile)

def main():
    # generate_golden()
    benchmarks_list = ["MG", "CG", "CG", "IS", "LU", "EP"]
    benchmark_commands = {
        "MG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/mg.A.8',
        "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/cg.A.8',
        "CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ft.A.8', 
        "IS" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/is.A.8',
        "LU" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/lu.A.8',
        "EP" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ep.A.8'
    }   
    while True:
        command = benchmark_commands["MG"]
        run_dict = remote_execute(command, 10)
        print(run_dict["DURATION_MS"])
                          
if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")   
        proc = main()
    except KeyboardInterrupt:
        print('Exiting program')
        sys.exit
        pass