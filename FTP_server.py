import socket, select, time, sys, os, threading

server_address = ('localhost', 5000)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(server_address)
server_socket.listen(10)

input_socket = [server_socket]
msg = ""
home = 'home' #ftp directory
user = 'progjar' #username
password = '123' #password

class FTPserver(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.aktif = home #direktori aktif
        self.user = '' #username input
        self.login = False #status login
        
try:
    ftp = FTPserver()
    while True:
        read_ready, write_ready, exception = select.select(input_socket, [], [])
        
        for sock in read_ready:
            if sock == server_socket:
                client_socket, client_address = server_socket.accept()
                input_socket.append(client_socket)        
            
            else:
                command = sock.recv(1024)
                print command.split()[0]
