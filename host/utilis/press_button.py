from GPIOClient import GPIOClient
import time
import sys

POWER_BUTTONS = {
    "0": 1, # Power button for setup 0
    "1": 3, # Power button for setup 1
    "2": 4, # Power button for setup 2
    "3": 5  # Power button for setup 3
}

RESET_BUTTONS = {
    "0": 2,  # Reset button for setup 0
    "1": 3,  # Reset button for setup 1
    "2": 4,  # Reset button for setup 2
    "3": 6   # Reset button for setup 3
}

REMOTE_GPIO_IP = "10.30.0.63"
REMOTE_GPIO_PORT = 18861

HELP_MSG = "Usage: button_simulator [OPTION]... [SETUP_ID]\n" + \
           " --reset-button [SETUP_ID]  Reset the setup specified in [SETUP_ID].\n" + \
           " --power-button [SETUP_ID]  Power up/down the setup specified in [SETUP_ID].\n" + \
           "Available setups: 0, 1, 2, 3" 

COMMANDS = ["--reset-button", "--power-button"]
SETUPS = ["0", "1", "2", "3"]

def push_button(relay_id: int, hold_time):
    try:
        client = GPIOClient(REMOTE_GPIO_IP, REMOTE_GPIO_PORT)
        client.connect()
        client.turn_on(relay_id)
        time.sleep(hold_time)
        client.turn_off(relay_id)
        client.disconnect()

    except Exception as e:
        print("Remote GPIO is down...")

def power_button(self, relay_id):
    push_button(relay_id, 4)

def reset_button(self, relay_id):
    push_button(relay_id, 2)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(HELP_MSG)
        exit(0)
    
    if sys.argv[1] in COMMANDS:
        if sys.argv[1] == COMMANDS[0]:
            if sys.argv[2] in SETUPS:
                reset_button(RESET_BUTTONS[sys.argv[2]])
            else:
                print(HELP_MSG)
        else:
            if sys.argv[2] in SETUPS:
                power_button(POWER_BUTTONS[sys.argv[2]])
            else:
                print(HELP_MSG)
    else:
        print(HELP_MSG)