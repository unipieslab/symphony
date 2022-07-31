
#!/usr/bin/env python
import sys # for exit
import socket
import pickle
from time import sleep

# def connect(connected, host, port):
#     clientSocket = socket.socket()    
#     while not connected:  
#         # attempt to reconnect, otherwise sleep for 0.1 seconds  
#         try:  
#             clientSocket.connect( ( host, port ) )  
#             connected = True  
#             print( "connection successful" )  
#         except socket.error:
#             print(socket.error)
#             connected = False   
#             sleep( 0.5 ) 
#         return connected, clientSocket 


def main():

    host = "127.0.0.1"  # Standard loopback interface address (localhost)
    port = 65431  # Port to listen on (non-privileged ports are > 1023)

    recon_counter = 0   
    dic_result = {
            'TIMESTAMP' : '',
            'STATE' : '',
            'STDOUT' : '', 
            'STDERROR': '',
            'RETURNCODE': '',
            'DMESG': '',
            'DURATION_MS': '',
            'FIRST_RUN' : ''
    }

    clientSocket = socket.socket()

    while True:
        try:  
            clientSocket.connect( ( host, port ) ) 
            clientSocket.send(bytes( "execute", "UTF-8" ))
            payload = b""
            while True:
                packet = clientSocket.recv(1024)
                if not packet: break
                payload += packet
            if payload != b"":
                dic_result = pickle.loads(payload)
            print(dic_result)
            clientSocket.close()
        except socket.error:
            
            print( "connection lost... reconnecting" )  
            while True:  
                # attempt to reconnect, otherwise sleep for 2 seconds  
                try:
                    print( "re-connecting" )   
                    clientSocket = socket.socket()   
                    clientSocket.connect( ( host, port ) ) 
                    print( "re-connection successful" )   
                    break
                except socket.error:  
                    sleep( 1 )  
        
                

if __name__ == '__main__':
    try:
        print("Press Ctrl-C to terminate")   
        proc = main()
    except KeyboardInterrupt:
        print('Exiting program')
        socket.close()
        sys.exit
        pass