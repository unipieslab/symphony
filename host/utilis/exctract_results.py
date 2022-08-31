import imp
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
        
file = '/home/dag/wsp/unipi/triumf/symphony/host/results/result_08_31_2022__20_19_47.json'
with open(file, 'r') as f:
    result = json.load(f)
    stdoutput = result["stdoutput"]
    print(stdoutput)

    try:
        verification_str = verification_regex.findall(stdoutput)
        answer = str(verification_str[0][1])
        answer = answer.strip()
        print(answer)
        if answer == "SUCCESSFUL":
            print("False") 
        else:
            print("True") 
    except Exception:
        print(verification_str)
        print(traceback.format_exc())
        


