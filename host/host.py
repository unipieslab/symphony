
#!/usr/bin/env python
import sys # for exit
import rpyc
from time import sleep
import serial
from serial.tools import list_ports #pyserial, esptool

def find_reset_uart():
    VID = '0403'
    PID = '6001'
    SERIAL_NUM = 'A50285BI'
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
    
ser = find_reset_uart()

def power_button():
    ser.dtr = True
    sleep(2)
    ser.dtr = False
    print("ACTION:POWER")


def reset_button():
    ser.rts = True
    sleep(1)
    ser.rts = False
    print("ACTION:RESET")

def main():
    # try_reconn_sec = 5
    # sleep_sec_excep = 0.5 
    # conn_count_thresh =  int(try_reconn_sec / sleep_sec_excep)
    # bench_timeout_sec = 2
    # run_command = "/usr/bin/sysbench cpu --time=1 --threads=2 run"
    # while True:   
    #     try:
    #         c = rpyc.connect("localhost", 18861)
    #         c._config['sync_request_timeout'] = bench_timeout_sec
    #         if not c.closed:
    #             try:
    #                 run_dict = c.root.execute(run_command) 
    #                 print(run_dict['DURATION_MS'])
    #                 c.close()
    #             except:
    #                 print("ERROR:RUN_TIMEOUT")
    #                 reset_button()              
    #     except:
    #         conn_count_thresh =  conn_count_thresh - 1
    #         print("connection_error_counter_thresh: " + str(conn_count_thresh))
    #         sleep(0.5)
    #         if conn_count_thresh <=0:
    #             reset_button()
    #             conn_count_thresh =  int(try_reconn_sec / sleep_sec_excep)
                          
if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")   
        proc = main()
    except KeyboardInterrupt:
        print('Exiting program')
        sys.exit
        pass