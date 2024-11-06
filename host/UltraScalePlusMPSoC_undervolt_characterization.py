from host import *

import math

g_current_voltage = 0.700 # Unit: mV

"""
    @param src The voltage value to convert to mantissa (to send on PMBus)
"""
def convert_to_mantissa(src: int):
    return math.ceil(src * 4096)
    
"""
    @param src: The mantissa to convert to voltage
"""
def convert_to_voltage(src: int):
    return src / 4096 

def undervolt_format() -> str:
    global g_current_voltage
    step = 0.010 # Unit: mV

    g_current_voltage = g_current_voltage - step
    mantissa = convert_to_mantissa(g_current_voltage)
    undervolt_command = "i2cset -f -y 0 0x13 0x21 {mantissa_hex} w".format(mantissa_hex=hex(mantissa))

    return undervolt_command

def get_voltage(src: Tester_Shell) -> str:
    voltage_command = "i2cget -f -y 0 0x13 0x8B w"

    mantissa = src.simple_remote_execute(voltage_command, 1, False)[0]["stdoutput"]

    return str(convert_to_voltage(int(mantissa.strip(), 16)))

def health_check(src: Tester_Shell) -> Tester_Shell_Health_Status:
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

def main():
    test = Tester_Shell()
    test.load_experiment_attr_from_json_file("UltraScalePlusMPSoC_undervolt_characterization.json")
    # Set the neccessery callbacks.
    test.set_callback(undervolt_format, Tester_Shell_Callback.UNDERVOLT_FORMAT)
    test.set_callback(get_voltage, Tester_Shell_Callback.REQUEST_VOLTAGE_VALUE)
    test.set_callback(health_check, Tester_Shell_Callback.DUT_HEALTH_CHECK)

    test.auto_undervolt_characterization(0.10, "PL UNDERVOLT")

if __name__ == '__main__':
    main()