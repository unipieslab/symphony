import rpyc

class GPIOClient:
    def __init__(self, server_ip, server_port):
        """
        Initializes a GPIOClient.

        :param server_ip: the IP address of the GPIO server.
        :param server_port: the port number of the GPIO server.
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.conn = None

    def connect(self):
        """
        Connects to the GPIO server.
        """
        try:
            self.conn = rpyc.connect(self.server_ip, self.server_port)
        except Exception as e:
            print(f"Could not connect to GPIO server at {self.server_ip}:{self.server_port}")
            print(f"Error details: {e}")
            self.conn = None

    def disconnect(self):
        """
        Disconnects from the GPIO server.
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def toggle_all(self, delay_sec):
        """
        Toggles all relays on the GPIO server.

        :param delay_sec: delay in seconds between toggle commands.
        :return: a string message from the server.
        """
        self.connect()
        result = self.conn.root.toggle_all(delay_sec)
        self.disconnect()
        return result

    def toggle_relay(self, relay_id, delay_sec):
        """
        Toggles a specific relay on the GPIO server.

        :param relay_id: the ID of the relay to toggle.
        :param delay_sec: delay in seconds between toggle commands.
        :return: a string message from the server.
        """
        self.connect()
        result = self.conn.root.toggle_relay(relay_id, delay_sec)
        self.disconnect()
        return result

    def turn_on(self, relay_id):
        """
        Turns on a specific relay on the GPIO server.

        :param relay_id: the ID of the relay to turn on.
        :return: a string message from the server.
        """
        self.connect()
        result = self.conn.root.turn_on(relay_id)
        self.disconnect()
        return result

    def turn_off(self, relay_id):
        """
        Turns off a specific relay on the GPIO server.

        :param relay_id: the ID of the relay to turn off.
        :return: a string message from the server.
        """
        self.connect()
        result = self.conn.root.turn_off(relay_id)
        self.disconnect()
        return result

    def get_relay_status(self, relay_id):
        """
        Gets the status of a specific relay on the GPIO server.

        :param relay_id: the ID of the relay to get the status of.
        :return: the status of the relay.
        """
        self.connect()
        status = self.conn.root.get_relay_status(relay_id)
        self.disconnect()
        return status
