from host import *
import re
import serial
import time

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

class UltraScalePlusMPSoC_Tester(Tester_Shell):
    def __init__(self):
        super().__init__()

        self.pl_temp = 0
        self.ps_temp = 0

        self.pl_watt = 0

    def is_result_correct(self, result: dict):
        pass

    def convert_to_voltage(self, src: int):
        return src / 4096 

    def get_voltage(self, src: Tester_Shell) -> str:
        voltage_command = "i2cget -f -y 0 0x13 0x8B w"

        mantissa = src.simple_remote_execute(voltage_command, 1, False)[0]["stdoutput"]

        return str(self.convert_to_voltage(int(mantissa.strip(), 16)))

    def target_reset_button(self):
        controller = Relay_Controller("ttyUSB0")
        controller.reset_computer()

    def target_class_system_err(self, addr: str):
        return None # TODO - Find a way to examine if the PL is down (or the whole system)

    def dut_monitor(self, healthlog: str):
        pl_temp_regex = "PL TEMP: (\d+.*)"
        ps_temp_regex = "PS TEMP: (\d+.*)"
        ps_watt_regex = "VCCINT.W.: (\d+).\d+"

        self.pl_temp = round(float(re.search(pl_temp_regex, healthlog).group(1)), 2)
        self.ps_temp = round(float(re.search(ps_temp_regex, healthlog).group(1)), 2)

        self.pl_watt = round(float(re.search(ps_watt_regex, healthlog).group(1)), 2)

    def additional_logs(self) -> str:
        return "PL Temp: " + str(self.pl_temp) + "(C) | PS Temp: " + str(self.ps_temp) + "(C)" \
               " | VCCINT power consumption: " + str(self.pl_watt) + "(W)"

def main():
    test = UltraScalePlusMPSoC_Tester()
    test.load_experiment_attr_from_json_file("UltraScalePlusMPSoC.json")

    test.debug_toggle_state_restore()
    test.debug_toggle_resets()

    test.set_callback(test.is_result_correct, Tester_Shell_Callback.IS_RESULT_CORRECT)
    test.set_callback(test.target_reset_button, Tester_Shell_Callback.TARGET_RESET_BUTTON)
    test.set_callback(test.get_voltage, Tester_Shell_Callback.REQUEST_VOLTAGE_VALUE)
    test.set_callback(test.additional_logs, Tester_Shell_Callback.ADDITIONAL_LOGS)
    test.set_callback(test.dut_monitor, Tester_Shell_Callback.DUT_MONITOR)

    try:
        test.target_perform_undervolt_test()
    except Exception:
        pass

if __name__ == '__main__':
    main()