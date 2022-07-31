
#!/usr/bin/env python
import sys # for exit
import rpyc
from time import sleep

def reset():
    print("ACTION:RESET")

def main():
    try_reconn_sec = 5
    sleep_sec_excep = 0.5 
    conn_count_thresh =  int(try_reconn_sec / sleep_sec_excep)
    bench_timeout_sec = 100
    run_command = "/usr/bin/sysbench cpu --time=1 --threads=2 run"
    while True:   
        try:
            c = rpyc.connect("localhost", 18861)
            c._config['sync_request_timeout'] = bench_timeout_sec
            if not c.closed:
                try:
                    run_dict = c.root.execute(run_command) 
                    print(run_dict['DURATION_MS'])
                    c.close()
                except:
                    print("ERROR:RUN_TIMEOUT")
                    reset()              
        except:
            conn_count_thresh =  conn_count_thresh - 1
            print("connection_error_counter_thresh: " + str(conn_count_thresh))
            sleep(0.5)
            if conn_count_thresh <=0:
                reset()
                conn_count_thresh =  int(try_reconn_sec / sleep_sec_excep)
                          
if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")   
        proc = main()
    except KeyboardInterrupt:
        print('Exiting program')
        sys.exit
        pass