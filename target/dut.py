from distutils.cmd import Command
import rpyc #pip3.9 install rpyc

from time import sleep
import sys # for exit
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass



class ExecuteService(rpyc.Service):
    
    def __init__(self):
        self.messages_file = '/var/log/messages'
        self.healthlog_file = '/var/log/healthlog'
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

    # My service
    def execute(self):
        print("Execute Request")
        return self.execute()
    
    def get_timestamp(self):
        now = datetime.now() # current day and time
        log_date = now.strftime("%m_%d_%Y__%H_%M_%S")
        return log_date
    
    def get_temp(self):
        command = "sensors | grep Tctl | awk '{printf $2}'"
        #command = "/root/triumf/symphony/target/bash_scripts/get_temp.sh"
        duration_ms, return_code, stderror, temp = self.sys_run(command)
        _ = duration_ms
        return temp
            
    def get_power(self):
        command = "sensors | grep SVI2_SoC | awk '{printf $2}'"
        #command = "/root/triumf/symphony/target/bash_scripts/get_power.sh"
        duration_ms, return_code, stderror, power = self.sys_run(command)
        _ = duration_ms
        return power
    
    def get_voltage(self):
        command = "sensors | grep SVI2_Core | awk '{printf $2}'"
        #command = "/root/triumf/symphony/target/bash_scripts/currvolt"
        duration_ms, return_code, stderror, currvolt = self.sys_run(command)
        _ = duration_ms
        return currvolt
    
    def get_freq(self):
        command = "cpupower frequency-info | grep Pstate-P0 | awk '{printf $2}'"
        #command = "/root/triumf/symphony/target/bash_scripts/currfreq"
        duration_ms, return_code, stderror, currfreq = self.sys_run(command)
        _ = duration_ms
        if return_code != 0:
            print(stderror)
        return currfreq

    def exposed_alive(self):
        return True
    
    def execute(self, run_command:str, dmesg_index:int):
        try:
            print("Executing: " + run_command)
            healthlog = "" 
            timestamp = "" 
            power = "" 
            temp = "" 
            voltage = "" 
            freq = "" 
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
            _, _, _, messages = self.sys_run("dmesg")
            dmesg_diff = messages[dmesg_index: len(messages)]
            duration_ms, return_code, stderror, stdoutput = self.sys_run(run_command)
            timestamp = self.get_timestamp() # current day and time
            power = self.get_power()
            temp = self.get_temp()
            voltage = self.get_voltage()
            freq = self.get_freq()
            healthlog = ""
    
            results = {
                "healthlog"   : healthlog,
                "run_command" : run_command,
                "timestamp"   : timestamp,
                "power"       : power,
                "temp"        : temp,
                "voltage"     : voltage,
                "freq"        : freq,
                "duration_ms" : duration_ms,
                "stdoutput"   : stdoutput,
                "stderror"    : stderror,
                "return_code" : return_code,
                "dmesg_diff"  : dmesg_diff
            }

            try:
                with open(self.healthlog_file, 'r') as f:
                    healthlog = f.read()
            except Exception:
                pass
            #return healthlog, run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff
            return results
        except Exception as exception:
            #return healthlog, run_command, timestamp, power, temp, voltage, freq, duration_ms, stdoutput, stderror, return_code, dmesg_diff
            return results
    
    def exposed_execute_n_times(self, run_command:str, dmesg_index:int, run_times:int):
        list_of_results = [] 
        results = dict() # initialize an empty dictionary. 
        # execute the command 'run_times' times.
        for times in range(run_times):
            try:
                results = self.execute(run_command, dmesg_index)
                list_of_results.append(results)
            except:
                pass 
        
        return list_of_results

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
