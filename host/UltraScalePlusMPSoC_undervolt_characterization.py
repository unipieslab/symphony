from host import *

import math

g_current_voltage = 0.850 # Unit: mV

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
    step = 0.002 # Unit: mV

    g_current_voltage = g_current_voltage - step
    mantissa = convert_to_mantissa(g_current_voltage)
    undervolt_command = "i2cset -f -y 0 0x13 0x21 {mantissa_hex} w".format(mantissa_hex=hex(mantissa))

    return undervolt_command

def get_voltage(src: Tester_Shell) -> str:
    voltage_command = "i2cget -f -y 0 0x13 0x8B w"

    mantissa = src.remote_execute(voltage_command, Tester_Shell_Constants.TIMEOUT_SCALE_VOLTAGE.value, 
                                  Tester_Shell_Constants.NETWORK_TIMEOUT_SEC.value, 0, 1, False)[0]["stdoutput"]

    return str(convert_to_voltage(int(mantissa.strip(), 16)))

def main():
    test = Tester_Shell()
    test.load_experiment_attr_from_json_file("UltraScalePlusMPSoC.json")

    # Set the neccessery callbacks.
    test.set_callback(undervolt_format, Tester_Shell_Callback.UNDERVOLT_FROMAT)
    test.set_callback(get_voltage, Tester_Shell_Callback.UNDERVOLT_VOLTAGE_VALUE)

    test.auto_undervolt_characterization(0.10, "PL UNDERVOLT")

if __name__ == '__main__':
    main()