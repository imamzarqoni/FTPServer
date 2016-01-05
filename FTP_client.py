import socket
import sys
import os

server_address = ('localhost', 5000)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(server_address)

sys.stdout.write(client_socket.recv(4096))
sys.stdout.write('>> ')

try:        
        while True:
                message = sys.stdin.readline()
                client_socket.send(message)
                if(message.split()[0].upper() == "RETR"):
                        message = message.split()
                        filename = ' '.join(message[1:])
                        i=0
                        iki=client_socket.recv(1024)
                        iki=iki.split('/r/n/r/n')
                        size=int(iki[0])
                        total='/r/n/r/n'.join(iki[1:])
                        size=size-len(total)
                        while i < size:
                            data = client_socket.recv(1024)
                            total=total+data
                            i=i+1024
                        f = open(filename,'wb')
                        f.write(total)
                        f.close()
                        client_socket.send('ok')
                elif(message.split()[0].upper() == "STOR"):
                        message = message.split()
                        filename = ' '.join(message[1:])
                        size = os.stat(filename).st_size
                        f = open(filename,'rb')
                        data = str(size)+'/r/n/r/n'
                        data = data+f.read()
                        client_socket.send(data)
                        f.close()
                elif(message.split()[0].upper() == "QUIT"):
                        sys.stdout.write(client_socket.recv(4096))
                        client_socket.close()
                        break
                sys.stdout.write(client_socket.recv(4096))
                sys.stdout.write('>> ')

except KeyboardInterrupt:
        client_socket.close()
        sys.exit(0)
