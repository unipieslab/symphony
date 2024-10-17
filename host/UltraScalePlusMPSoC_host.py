from host import *
import re
import serial
import time

class UltraScalePlusMPSoC_Tester(Tester_Shell):
    pass

class Relay_Controller():
    # Initialize the controller
    # @param dev The device of the UART module.
    def __init__(self, dev):
        self.dev = "/dev/"+dev
        self.ser = serial.Serial(self.dev)
        self.ser.setRTS(False) # Initialize RTS
        self.ser.setDTR(False) # Initialize DTR

    def reset_computer(self):
        self.ser.setRTS(True)
        time.sleep(1)
        self.ser.setRTS(False)

def is_result_correct(result: dict):
    pass

def target_reset_button():
    controller = Relay_Controller("ttyUSB4")
    controller.reset_computer()

def target_class_system_err(addr: str):
    return None # TODO - Find a way to examine if the PL is down (or the whole system)


def main():
    test = UltraScalePlusMPSoC_Tester()
    test.load_experiment_attr_from_json_file("UltraScalePlusMPSoC.json")

    test.debug_toggle_state_restore()

    test.set_callback(is_result_correct, Tester_Shell_Callback.IS_RESULT_CORRECT)
    test.set_callback(target_reset_button, Tester_Shell_Callback.TARGET_RESET_BUTTON)
    test.set_callback(target_class_system_err, Tester_Shell_Callback.TARGET_CLASS_SYSTEM_ERR)

    try:
        test.target_perform_undervolt_test()
    except Exception:
        pass

if __name__ == '__main__':
    main()