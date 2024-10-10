from distutils.cmd import Command
import rpyc #pip3.9 install rpyc

from time import sleep
import sys # for exit
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass
import orjson
import re
import threading

class ExecuteService(rpyc.Service):
    
    def __init__(self):
        self.messages_file      = '/var/log/messages'
        self.stop_monitor_th    = None
        self.monitor_data       = ""
        self.monitor_data_sleep = 0.05

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

    # My service
    def execute(self):
        print("Execute Request")
        return self.execute()
    
    def get_timestamp(self):
        now = datetime.now() # current day and time
        log_date = now.strftime("%m_%d_%Y__%H_%M_%S")
        return log_date
    
    def monitor_routine_th(self):
        """
            'th' stands for Thread, because this function
            is executing inside a thread (in order to calculate avg values in parallel
            with the currently executing benchmark).
        """
        command = "sensors"
        self.monitor_data = ""
        while not self.stop_monitor_th.is_set():
            sleep(self.monitor_data_sleep)
            duration_ms, return_code, stderror, monotired_data = self.sys_run(command)
            self.monitor_data += monotired_data

    def get_freq(self):
        command = "cat /proc/cpuinfo | grep MHz"
        duration_ms, return_code, stderror, currfreq = self.sys_run(command)

        return currfreq   

    def exposed_alive(self):
        return True

    def execute(self, run_command:str, dmesg_index:int):
        try:
            healthlog = "" 
            timestamp = "" 
            duration_ms = "" 
            stdoutput = "" 
            stderror = "" 
            return_code = "" 
            dmesg_diff = ""
            messages = ""
            results = dict()
            # try:
            #     with open(self.messages_file, 'r') as f:
            #         messages = f.read()
            # except Exception:
            #     pass
            _, _, _, messages = self.sys_run("dmesg --ctime")
            dmesg_diff = messages[dmesg_index: len(messages)]

            self.stop_monitor_th = threading.Event()
            monitor_th = threading.Thread(target=self.monitor_routine_th, args=[])
            # Start the thread.
            monitor_th.start()
            
            duration_ms, return_code, stderror, stdoutput = self.sys_run(run_command)
            self.stop_monitor_th.set()
            monitor_th.join()
            self.stop_monitor_th.clear()

            timestamp = self.get_timestamp() # current day and time
            healthlog = ""
            healthlog += self.monitor_data
            healthlog += self.get_freq()

            results = {
                "healthlog"   : healthlog,
                "run_command" : run_command,
                "timestamp"   : timestamp,
                "duration_ms" : duration_ms,
                "stdoutput"   : stdoutput,
                "stderror"    : stderror,
                "return_code" : return_code,
                "dmesg_diff"  : dmesg_diff
            }

            return results
        except Exception as exception:
            return results
    
    def exposed_execute_n_times(self, run_command:str, dmesg_index:int, run_times:int):
        list_of_results = [] 
        results = dict() # initialize an empty dictionary. 
        # execute the command 'run_times' times.
        for times in range(run_times):
            print("Executing: " + run_command + ", Run: " + str(times))
            try:
                results = self.execute(run_command, dmesg_index)
                list_of_results.append(results)
            except:
                pass 
        data = orjson.dumps(list_of_results)
        return data

    def sys_run(self, cmd):
        t1 = datetime.now()
        process = subprocess.run([cmd], capture_output=True, shell=True)
        t2 = datetime.now()
        delta = t2 - t1
        duration_ms = str(round(delta.total_seconds() * 1000))
        return_code = str(process.returncode)
        if return_code != '0':
            print(stderror)
        stderror = process.stderr.decode("utf-8")
        stdoutput = process.stdout.decode("utf-8")
        return duration_ms, return_code, stderror, stdoutput

if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")
        from rpyc.utils.server import ThreadPoolServer 
        server = ThreadPoolServer(ExecuteService, port=18861, protocol_config={'allow_public_attrs': True})
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
