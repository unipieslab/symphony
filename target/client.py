from multiprocessing.reduction import ACKNOWLEDGE
from transitions import Machine
from time import sleep
import sys # for exit
import socket
import subprocess
import json
from datetime import datetime, timedelta

# configure socket and connect to server  
clientSocket = socket.socket()  
#host = socket.gethostname()  
#port = 25000  
host = "127.0.0.1"  # Standard loopback interface address (localhost)
port = 65432  # Port to listen on (non-privileged ports are > 1023)


class Fsm(object):

    states = ['state_wait', 'state_execute', 'state_error']
    first_run = True
    dmesg_length = 0
    def __init__(self, run_command):
        self.__run_command = run_command
        # Initialize the state machine
        self.machine = Machine(model=self, states=Fsm.states, initial='state_wait')
        self.machine.add_transition(trigger='execute', source='state_wait', dest='state_execute', after='execute')

    def sys_run(self, cmd):
        t1 = datetime.now()
        process = subprocess.run([cmd], capture_output=True, shell=True)
        t2 = datetime.now()
        delta = t1 - t2
        duration_ms = delta.total_seconds() * 1000

        return_code = str(process.returncode)
        stderror = process.stderr.decode("utf-8")
        stdoutput = process.stdout.decode("utf-8")
        return duration_ms, return_code, stderror, stdoutput
    
    def get_json(self, state, now, return_code, stderror, stdoutput, dmesg, duration_ms):
        run_json = {
            'TIMESTAMP' : '',
            'STATE' : '',
            'STDOUT' : '', 
            'STDERROR': '',
            'RETURNCODE': '',
            'DMESG': '',
            'DURATION_MS': ''
        }
        run_json['STATE'] = state
        run_json['TIMESTAMP'] = now
        run_json['STDOUT'] = stdoutput
        run_json['STDERROR'] = stderror
        run_json['RETURNCODE'] = return_code 
        run_json['DMESG'] = dmesg
        run_json['DURATION_MS'] = duration_ms
        return run_json


    def boot_init(self):
        return_code, stderror, stdoutput = self.sys_run(self.__run_command)


    def time_stamp(self):
        now = datetime.now() # current date and time
        log_date = now.strftime("%m_%d_%Y__%H_%M_%S.%f")[:-3]
        return log_date
    def execute(self):
        print("Executing benchmark")
        
        dmesg_diff = ""
        if self.first_run == True:
            self.first_run = False
            _, _, _, dmesg = self.sys_run("dmesg")
            self.dmesg_length = len(dmesg)
            dmesg_diff = dmesg
        else:
            _, _, _, dmesg = self.sys_run("dmesg")
            dmesg_diff = dmesg[self.dmesg_length: len(dmesg)]
            self.dmesg_length = len(dmesg)

        duration_ms, return_code, stderror, stdoutput = self.sys_run(self.__run_command) 
        now = self.time_stamp()      
        print(dmesg_diff)

        
    

# Global Variables

run_command = "/usr/bin/sysbench cpu --time=1 --threads=2 run"
fsm = Fsm(run_command)

def main():


    # clientSocket.connect( ( host, port ) )  
    
    # # keep track of connection status  
    # connected = True  
    # print( "connected to server" )  

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