ps -ef | grep dut.py | grep -v grep | awk '{print $2}' | xargs kill
