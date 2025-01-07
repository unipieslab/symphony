from GPIOClient import GPIOClient
import time

def dut_reset():
    remote_reset = GPIOClient("192.168.200.3", 18861)
    relay_id = 1

    remote_reset.turn_on(relay_id)
    time.sleep(3)
    remote_reset.turn_off(relay_id)

dut_reset()
