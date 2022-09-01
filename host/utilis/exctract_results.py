import json
import re
import sys
import traceback
# result = {
#     "timestamp" : timestamp,
#     "run_command": run_command,
#     "return_code" : return_code,
#     "correct" : correct,
#     "duration_ms" : duration_ms,
#     "power" : power,
#     "temp" : temp,
#     "voltage" : voltage,
#     "freq" : freq,
#     "stdoutput" : stdoutput,
#     "stderror" : stderror,
#     "dmesg_diff" : dmesg_diff
# }

regex = r'Verification( +)=(. +.*)'
verification_regex = re.compile(regex, re.IGNORECASE)
        
file = '/home/dag/wsp/unipi/triumf/symphony/host/results/result_08_31_2022__23_39_54.json'
with open(file, 'r') as f:
    result = json.load(f)
    stdoutput = result["power"]
    print(stdoutput)

    # try:
    #     verification_str = verification_regex.findall(stdoutput)
    #     answer = str(verification_str[0][1])
    #     answer = answer.strip()
    #     print(answer)
    #     if answer == "SUCCESSFUL":
    #         print("False") 
    #     else:
    #         print("True") 
    # except Exception:
    #     print(verification_str)
    #     print(traceback.format_exc())
        
    regex = r'.*?PMD=(.*), SoC=(.*), DIMM1=(.*), DIMM2=(.*$)'
    power_regex = re.compile(regex, re.IGNORECASE)
    power_str = power_regex.findall(stdoutput)
    power_pmd = float(power_str[0][0])
    power_soc = float(power_str[0][1])
    power_dimm1 = float(power_str[0][2])
    power_dimm2 = float(power_str[0][3])

    
    stdoutput = result["voltage"]

    CURRENT_PMD_THRESHOLD = 16.00 #15.28 
    CURRENT_SOC_THRESHOLD = 8.50 #7.97
    TEMP_PMD_THRESHOLD = 75 #63
    TEMP_SOC_THRESHOLD = 75 #60 
    TEMP_DIMM1_THRESHOLD = 75 #64
    POWER_DIMM1_THRESHOLD = 7.2 #6.745

    regex = r'.*?PMD:(.*)SoC:(.*$)'
    voltage_regex = re.compile(regex, re.IGNORECASE)
    stdoutput = str(stdoutput).replace("\n","")
    voltage_str = voltage_regex.findall(stdoutput)
    voltage_pmd = round((float(voltage_str[0][0])/1000),3)
    voltage_soc = round((float(voltage_str[0][1])/1000),3)
    current_pmd = round((power_pmd / (voltage_pmd)),2)
    current_soc = round((power_soc / (voltage_soc)),2)

    temp = result["temp"]
    regex = r'.*?PMD=(.*),.*?=(.*),.*?=(.*)'
    temp_regex = re.compile(regex, re.IGNORECASE)
    temp_str = temp_regex.findall(temp)
    temp_pmd = int(temp_str[0][0])
    temp_soc = int(temp_str[0][1])
    temp_dimm = int(temp_str[0][2])

    power_curr_volt_temp_str = "MONITOR: PMD = "+ str(power_pmd) + "(W)/" + str(current_pmd) + "(A)/" + str(voltage_pmd) +"(V)/" \
        + str(temp_pmd)+"(C) | SoC = "+ str(power_soc) + "(W)/" + str(current_soc) + "(A)/" + str(voltage_soc) +"(V)/" + str(temp_soc)+"(C)" \
            + " | DIMM1 = "+ str(power_dimm1) + "(W)/" + str(temp_dimm)+"(C)" 

    if current_pmd > CURRENT_PMD_THRESHOLD:
        print("PMD overcurrent: " + str(current_pmd) + "(A)")
    if current_soc > CURRENT_SOC_THRESHOLD:
        print("SOC overcurrent: " + str(current_soc) + "(A)")
    if power_dimm1 > POWER_DIMM1_THRESHOLD:
        print("SOC overpower: " + str(power_dimm1) + "(W)")
    if temp_pmd > TEMP_PMD_THRESHOLD:
        print("PMD over temperature: " + str(temp_pmd) + "(C)")
    if temp_soc > TEMP_SOC_THRESHOLD:
        print("SOC over temperature: " + str(temp_soc) + "(C)")
    if temp_dimm > TEMP_DIMM1_THRESHOLD:
        print("SOC over temperature: " + str(temp_dimm) + "(C)")
    
    
    print(power_curr_volt_temp_str)
    

    error_consecutive = 1
    RESET_AFTER_CONCECUTIVE_ERRORS = 2

    if error_consecutive == RESET_AFTER_CONCECUTIVE_ERRORS:
                    print("reset_button()")

    if error_consecutive >= (RESET_AFTER_CONCECUTIVE_ERRORS + 1):
        print("self.power_cycle(True)")

