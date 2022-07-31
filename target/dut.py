from multiprocessing.reduction import ACKNOWLEDGE
from transitions import Machine
from time import sleep
import sys # for exit
import socket
import subprocess
import pickle
from datetime import datetime, timedelta 

class Fsm(object):

    def __init__(self, run_command):
        self.states = ['state_wait', 'state_execute', 'state_error']
        self.first_run = True
        self.dmesg_length = 0
        self.__run_command = run_command
        # Initialize the state machine
        self.machine = Machine(model=self, states=self.states, initial='state_wait')
        self.machine.add_transition(trigger='execute', source='state_wait', dest='state_execute', before='receive_cmd', after='execute')

    def sys_run(self, cmd):
        t1 = datetime.now()
        process = subprocess.run([cmd], capture_output=True, shell=True)
        t2 = datetime.now()
        delta = t2 - t1
        duration_ms = round(delta.total_seconds() * 1000)

        return_code = str(process.returncode)
        stderror = process.stderr.decode("utf-8")
        stdoutput = process.stdout.decode("utf-8")
        return duration_ms, return_code, stderror, stdoutput
    
    def get_json(self, state, now, return_code, stderror, stdoutput, dmesg, duration_ms, first_run):
        run_json = {
            'TIMESTAMP' : '',
            'STATE' : '',
            'STDOUT' : '', 
            'STDERROR': '',
            'RETURNCODE': '',
            'DMESG': '',
            'DURATION_MS': '',
            'FIRST_RUN' : ''
        }
        run_json['STATE'] = state
        run_json['TIMESTAMP'] = now
        run_json['STDOUT'] = stdoutput
        run_json['STDERROR'] = stderror
        run_json['RETURNCODE'] = return_code 
        run_json['DMESG'] = dmesg
        run_json['DURATION_MS'] = duration_ms
        run_json['FIRST_RUN'] = first_run
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
        first_run = "1"
        dic_result = self.get_json(self.state, now, return_code, stderror, stdoutput, dmesg_diff, duration_ms, first_run)
        return dic_result

        

# Global Variables



def main():
    run_command = "/usr/bin/sysbench cpu --time=1 --threads=2 run"
    fsm = Fsm(run_command)

    host = "127.0.0.1"  # Standard loopback interface address (localhost)
    port = 65431  # Port to listen on (non-privileged ports are > 1023)

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((host, port))
    serverSocket.listen()
    connection, _ = serverSocket.accept()

    while True:  
        # attempt to send and receive wave, otherwise reconnect  
        try:
            message = connection.recv( 1024 ).decode( "UTF-8" )
            if message == "execute":
                dic_result = fsm.execute() 
                payload = pickle.dumps(dic_result)
                connection.sendall(payload)
        except socket.error:  
            serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverSocket.bind((host, port))
            serverSocket.listen()
            connection, _ = serverSocket.accept()


if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")   
        proc = main()
    except KeyboardInterrupt:
        print('Exiting program')                  
        clientSocket.close();  
        sys.exit
        pass