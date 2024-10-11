from host import *

class UltraScalePlusMPSoC_Tester(Tester_Shell):
    pass

g_is_first_result: bool = True
g_first_result: str = ""
g_result_benchmark: str = ""


def is_result_correct(result: dict):
    global g_is_first_result
    global g_first_result
    global g_result_benchmark

    if not g_is_first_result and result["run_command"] != g_result_benchmark:
        g_is_first_result = True

    if g_is_first_result:
        g_is_first_result  = False
        g_result_benchmark = result["run_command"]
        g_first_result     = result["stdoutput"]

    

    return True

def target_reset_button():
    pass

def target_class_system_err(addr: str):
    pass


def main():
    test = UltraScalePlusMPSoC_Tester()
    test.load_experiment_attr_from_json_file("UltraScalePlusMPSoC.json")

    test.set_callback(is_result_correct, Tester_Shell_Callback.IS_RESULT_CORRECT)

    test.target_perform_undervolt_test()

if __name__ == '__main__':
    main()