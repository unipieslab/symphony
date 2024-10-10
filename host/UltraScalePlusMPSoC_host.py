from host import *

class UltraScalePlusMPSoC_Tester(Tester_Shell):
    pass


def main():
    test = UltraScalePlusMPSoC_Tester()
    test.load_experiment_attr_from_json_file("UltraScalePlusMPSoC.json")

    test.target_perform_undervolt_test()

if __name__ == '__main__':
    main()