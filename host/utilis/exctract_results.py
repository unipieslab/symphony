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
        
file = '/home/dag/wsp/unipi/triumf/symphony/host/results/result_09_02_2022__10_48_25.json'
file = '/home/eslab/wsp/unipi/triumf/symphony/host/results/MG_V980_09_04_2022__17_11_47.json'
file = '/home/eslab/wsp/unipi/triumf/symphony/host/results/MG_V980_09_04_2022__17_11_44.json'
with open(file, 'r') as f:
    result = json.load(f)
    stdoutput = result["dmesg_diff"]
    print(stdoutput)
        


