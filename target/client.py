from multiprocessing.reduction import ACKNOWLEDGE
from transitions import Machine
from time import sleep
import sys # for exit
import socket
import subprocess
import json
from datetime import datetime



HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

run_dict = {
    'TIMESTAMP' : '',
    'STATE' : '',
    'STDOUT' : '', 
    'STDERROR': '',
    'RETURNCODE': '',
    'DMESG': ''
}


def sys_run(cmd):
        process = subprocess.run([cmd], capture_output=True, shell=True)
        return_code = str(process.returncode)
        stderror = process.stderr.decode("utf-8")
        stdoutput = process.stdout.decode("utf-8")
        return return_code, stderror, stdoutput

def time_stamp():
    now = datetime.now() # current date and time
    log_date = now.strftime("%m_%d_%Y__%H_%M_%S.%f")[:-3]
    return log_date


class Fsm(object):

    states = ['state_booted', 'state_warm', 'state_wait', 'state_execute', 'state_error']

    def __init__(self):


        # Initialize the state machine
        self.machine = Machine(model=self, states=Fsm.states, initial='state_booted')

        self.machine.add_transition(trigger='go_warm', source='state_booted', dest='state_warm', after='exec_warm_up')
        self.machine.add_transition(trigger='go_wait', source=['state_warm', 'state_wait'], dest='state_wait')
        self.machine.add_transition(trigger='go_execute', source='state_wait', dest='state_execute', after='execute')

    def exec_warm_up(self):
        print("Warming")
        fsm.go_wait()
        
  
    def execute(self):

        print("Executing benchmark")
        run_dict['STATE'] = self.state
        run_dict['TIMESTAMP'] = time_stamp() 
        cmd = "/usr/bin/sysbench cpu --time=1 --threads=2 run"
        return_code, stderror, stdoutput = sys_run(cmd)
        # print("STDOUT: " + stdoutput)
        # print("STDERROR: " + stderror)
        # print("RETURNCODE: " + return_code)
        run_dict['STDOUT'] = stdoutput
        run_dict['STDERROR'] = stderror
        run_dict['RETURNCODE'] = return_code

        return_code, stderror, stdoutput = sys_run("dmesg")
        dmesg = stdoutput
        run_dict['DMESG'] = dmesg

        s1 = json.dumps(run_dict)
        fsm.go_wait()

# Global Variables
fsm = Fsm()

def main():
    
    fsm.go_warm()

    while True:
        if fsm.state == 'state_wait':
            print(fsm.state)
            fsm.execute()

if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")   
        proc = main()
    except KeyboardInterrupt:
        print('Exiting program')
        sys.exit
        pass