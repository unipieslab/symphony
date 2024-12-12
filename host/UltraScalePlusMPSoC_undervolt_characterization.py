from host import *
from GPIOClient import GPIOClient
import os

import math

class UltraScalePlusMPSoC_Tester_Undervolt(Tester_Shell):
    def __init__(self):
        super().__init__()
        self.current_voltage = 0.850

    """
        @param src The voltage value to convert to mantissa (to send on PMBus)
    """
    def convert_to_mantissa(self, src: int):
        return math.ceil(src * 4096)
    
    """
        @param src: The mantissa to convert to voltage
    """
    def convert_to_voltage(self, src: int):
        return src / 4096 

    def undervolt_format(self) -> str:
        step = 0.001 # Unit: mV

        mantissa = self.convert_to_mantissa(self.current_voltage)
        undervolt_command = "i2cset -f -y 0 0x13 0x21 {mantissa_hex} w".format(mantissa_hex=hex(mantissa))

        self.current_voltage = self.current_voltage - step
        return undervolt_command

    def get_voltage(self, src: Tester_Shell) -> str:
        voltage_command = "i2cget -f -y 0 0x13 0x8B w"

        mantissa = src.simple_remote_execute(voltage_command, 1, False)[0]["stdoutput"]

        return str(self.convert_to_voltage(int(mantissa.strip(), 16)))

    def health_check(self, src: Tester_Shell) -> Tester_Shell_Health_Status:
        dpu_crash_indicator = "Check failed"
        health_check_cmd = "/home/root/downloads/Vitis-AI/examples/Vitis-AI-Library/samples/medicaldetection/test_jpeg_medicaldetection                     \
                            /usr/share/vitis_ai_library/models/pruned_experiment/RefineDet-Medical_EDD_pruned_0_5_tf.xmodel                                 \
                            /home/root/benchmarks/EndoCV2020-Endoscopy-Disease-Detection-Segmentation-subChallenge_data/originalImages/EDD2020_B0089.jpg"

        result = src.simple_remote_execute(health_check_cmd, 1, False)[0]
        stdoutput = result["stdoutput"]
        stderror  = result["stderror"]

        if (dpu_crash_indicator in stdoutput or dpu_crash_indicator in stderror):
            return Tester_Shell_Health_Status.DAMAGED
    
        return Tester_Shell_Health_Status.HEALTHY

    def dut_reset(self):
        os.system("/bin/python3.10 ./reset.py")

def main():
    test = UltraScalePlusMPSoC_Tester_Undervolt()
    test.load_experiment_attr_from_json_file("UltraScalePlusMPSoC_undervolt_characterization.json")

    # Set the neccessery callbacks.
    test.set_callback(test.undervolt_format, Tester_Shell_Callback.UNDERVOLT_FORMAT)
    test.set_callback(test.get_voltage, Tester_Shell_Callback.REQUEST_VOLTAGE_VALUE)
    test.set_callback(test.health_check, Tester_Shell_Callback.DUT_HEALTH_CHECK)
    test.set_callback(test.dut_reset, Tester_Shell_Callback.TARGET_RESET_BUTTON)

    test.auto_undervolt_characterization(0.10, "PL UNDERVOLT")

if __name__ == '__main__':
    main()