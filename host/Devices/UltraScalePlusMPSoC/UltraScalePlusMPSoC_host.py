import sys
sys.path.insert(1, '../../../host')

from host import *
import re

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
        os.system("/bin/python3.11 ./reset.py")

    def dut_monitor(self, healthlog: str):
        pl_temp_regex = "PL TEMP: (\d+.*)"
        ps_temp_regex = "PS TEMP: (\d+.*)"
        ps_watt_regex = "VCCINT.W.: (\d+).\d+"

        self.pl_temp = round(float(re.search(pl_temp_regex, healthlog).group(1)), 2)
        self.ps_temp = round(float(re.search(ps_temp_regex, healthlog).group(1)), 2)

        self.pl_watt = round(float(re.search(ps_watt_regex, healthlog).group(1)), 2)

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

    def additional_logs(self) -> str:
        return "PL Temp: " + str(self.pl_temp) + "(C) | PS Temp: " + str(self.ps_temp) + "(C)" \
               " | VCCINT power consumption: " + str(self.pl_watt) + "(W)"

def main():
    test = UltraScalePlusMPSoC_Tester()
    test.load_experiment_attr_from_json_file("UltraScalePlusMPSoC.json")

    # test.debug_toggle_state_restore()
    # test.debug_toggle_resets()

    test.set_callback(test.is_result_correct, Tester_Shell_Callback.IS_RESULT_CORRECT)
    test.set_callback(test.target_reset_button, Tester_Shell_Callback.TARGET_RESET_BUTTON)
    test.set_callback(test.get_voltage, Tester_Shell_Callback.REQUEST_VOLTAGE_VALUE)
    test.set_callback(test.additional_logs, Tester_Shell_Callback.ADDITIONAL_LOGS)
    test.set_callback(test.dut_monitor, Tester_Shell_Callback.DUT_MONITOR)
    test.set_callback(test.health_check, Tester_Shell_Callback.DUT_HEALTH_CHECK)

    try:
        test.target_perform_undervolt_test()
    except Exception:
        pass

if __name__ == '__main__':
    main()
