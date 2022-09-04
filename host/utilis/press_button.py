
import traceback

from time import sleep
import serial
from serial.tools import list_ports #pyserial, esptool
from datetime import datetime
import logging
from time import time
from datetime import timedelta

#Global variables
now = datetime.now() # current date and time
log_date = now.strftime("%m_%d_%Y__%H_%M_%S")
log_file_name = '/home/eslab/wsp/unipi/triumf/symphony/host/utilis/logs_power_button/log_' + log_date + '.log'
# logging.INFO
logging.basicConfig(filename=log_file_name, encoding='utf-8', format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s' \
    ,level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                      datefmt='%Y-%m-%d,%H:%M:%S')

screen_handler = logging.StreamHandler()
logging.getLogger().addHandler(screen_handler)


def power_button():
    # Reset UART INFO
    VID = '0403'
    PID = '6001'
    SERIAL_NUM = 'A50285BI'
    ser = find_reset_uart(VID, PID, SERIAL_NUM)
    if ser != None:
        ser.dtr = True
        logging.warning("power_button pressed")
        sleep(1)
        ser.dtr = False
        logging.warning("power_button reseased")
        ser.close()
    

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
            ser.dtr = False
            ser.rts = False
            logging.info("Opening serial port:" + port + " @" + BAUDRATE)
            
            return ser
           
        except Exception:
            logging.warning(traceback.format_exc())
            if port == None:
                logging.warning("Cannot find reset UART")
                pass
            
power_button()