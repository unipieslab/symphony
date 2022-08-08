import rpyc #pip3.9 install rpyc

from time import sleep
import sys # for exit
import subprocess
from datetime import datetime, timedelta

class ExecuteService(rpyc.Service):

    def __init__(self):
        pass

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

    def get_dict(self, run_command:str, now:str, return_code:str, stderror:str, stdoutput:str, dmesg:str, duration_ms:str):
        run_dict = {
            'RUN_COMMAND' : '',
            'TIMESTAMP' : '',
            'STDOUT' : '', 
            'STDERROR': '',
            'RETURNCODE': '',
            'DMESG': '',
            'DURATION_MS': ''
        }
        run_dict['RUN_COMMAND'] = run_command
        run_dict['TIMESTAMP'] = now
        run_dict['STDOUT'] = stdoutput
        run_dict['STDERROR'] = stderror
        run_dict['RETURNCODE'] = return_code 
        run_dict['DMESG'] = dmesg
        run_dict['DURATION_MS'] = duration_ms
        return run_dict


    # My service
    def execute(self):
        print("Execute Request")
        return self.execute()
    
    def time_stamp(self):
        now = datetime.now() # current day and time
        log_date = now.strftime("%m_%d__%H_%M_%S") 
        return log_date
    
    def exposed_execute(self, run_command:str):
        print("Executing: " + run_command)
        _, _, _, dmesg = self.sys_run("dmesg")
        dmesg_diff = dmesg #dmesg[dmesg_index: len(dmesg)]
        duration_ms, return_code, stderror, stdoutput = self.sys_run(run_command)
        now = self.time_stamp() # current day and time
        dic_result = self.get_dict(run_command, now, return_code, stderror, stdoutput, dmesg_diff, str(duration_ms))
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
        
        
        # server = ThreadPoolServer(ExecuteService, port=18861, nbThreads=1, requestBatchSize=1)
        # server.start()
        # while True:
        #     server = OneShotServer(ExecuteService, port=18861)
        #     server.start()
    except KeyboardInterrupt:
        print('Exiting program')                  
        server.close()
        sys.exit
        pass