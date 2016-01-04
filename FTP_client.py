import socket
import sys
import os

server_address = ('localhost', 5000)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(server_address)

sys.stdout.write('>> ')

try:
        while True:
                message = sys.stdin.readline()
                client_socket.send(message)
                
except KeyboardInterrupt:
        client_socket.close()
        sys.exit(0)
