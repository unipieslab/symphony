import rpyc

from time import sleep
import sys # for exit
import subprocess
from datetime import datetime, timedelta



class ExecuteService(rpyc.Service):

    def __init__(self):
        self.first_run = True
        self.dmesg_length = 0
        self.iteration = 0

    def on_connect(self, conn):
        # code that runs when a connection is created
        # (to init the service, if needed)
        print("Client Connected")
        pass

    def on_disconnect(self, conn):
        # code that runs after the connection has already closed
        # (to finalize the service, if needed)
        print("Client Disconnected")
        pass

    def get_dict(self, run_command, now, return_code, stderror, stdoutput, dmesg, duration_ms, first_run):
        run_dict = {
            'RUN_COMMAND' : '',
            'TIMESTAMP' : '',
            'STDOUT' : '', 
            'STDERROR': '',
            'RETURNCODE': '',
            'DMESG': '',
            'DURATION_MS': '',
            'FIRST_RUN' : ''
        }
        run_dict['RUN_COMMAND'] = run_command
        run_dict['TIMESTAMP'] = now
        run_dict['STDOUT'] = stdoutput
        run_dict['STDERROR'] = stderror
        run_dict['RETURNCODE'] = return_code 
        run_dict['DMESG'] = dmesg
        run_dict['DURATION_MS'] = duration_ms
        run_dict['FIRST_RUN'] = first_run
        return run_dict


    # My service
    def execute(self):
        print("Execute Request")
        return self.execute()
    
    def time_stamp(self):
        now = datetime.now() # current date and time
        log_date = now.strftime("%m_%d_%Y__%H_%M_%S.%f")[:-3] 
        return log_date

    def exposed_execute(self, run_command):
        print("Run[" + str(self.iteration) + "]: " + run_command)
        self.iteration = self.iteration + 1
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
        duration_ms, return_code, stderror, stdoutput = self.sys_run(run_command) 
        now = self.time_stamp()
        first_run = "0" 
        if self.first_run == True:
            first_run = "1"

        dic_result = self.get_dict(run_command, now, return_code, stderror, stdoutput, dmesg_diff, duration_ms, first_run)
        return dic_result
    
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

if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")
        from rpyc.utils.server import ThreadPoolServer 
        server = ThreadPoolServer(ExecuteService, port=18861)
        server.start()
        #server = ThreadPoolServer(ExecuteService, port=18861, nbThreads=1, requestBatchSize=1)
        #server.start()
        # while True:
        #     server = OneShotServer(ExecuteService, port=18861)
        #     server.start()
    except KeyboardInterrupt:
        print('Exiting program')                  
        server.close()
        sys.exit
        pass