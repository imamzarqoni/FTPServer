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
    
    def ftp_pwd(self):
        #Mencetak direktori aktif (PWD: 4.1.3)
        if(self.login):
            dirs = os.path.relpath(self.aktif,home)
            if dirs == ".":
                dirs = "/"
            else:
                dirs = "/" + dirs
            msg = "257 \"" + dirs + "\"\r\n"
            return msg
        else:
            return '530 Please log in with USER and PASS first.\r\n'

    def ftp_cwd(self,args):
        #Mengubah direktori aktif (CWD: 4.1.1)
        if(self.login):
            msg = "250 Directory successfully changed."
            if(args == ".."):
                if self.aktif != home:
                    self.aktif = "/".join(self.aktif.split("/")[:-1])
                    print self.aktif
                else:
                    self.aktif = home
                    print self.aktif
                return msg
            else:
                if(args=="/"):
                    self.aktif = home
                    print self.aktif
                    if(os.path.isdir(self.aktif)):
                        return msg
                    else:
                        return "550 Failed to change directory."
                else:
                    if(args[0]=="/"):
                        self.aktif = home + args
                    else:
                        self.aktif = self.aktif + "/" + args
                    print self.aktif
                    if(os.path.isdir(self.aktif)):
                        return msg
                    else:
                        return "550 Failed to change directory."
        else:
            return '530 Please log in with USER and PASS first.\r\n'

    def ftp_mkd(self,args):
        #Membuat direktori (MKD: 4.1.3)
        if(self.login):
            if(args[0]=="/"):
                new_dir = home + args
            else:
                new_dir = self.aktif + "/" + args
            if(os.path.isdir(new_dir)):
                return "550 Create directory operation failed."
            else:
                os.makedirs(new_dir)
                dirs = os.path.relpath(new_dir,home)
                if dirs == ".":
                    dirs = "/"
                else:
                    dirs = "/" + dirs
                msg = "257 \"" + dirs + "\" created"
                return msg
        else:
            return '530 Please log in with USER and PASS first.\r\n'
            
    def ftp_rmd(self,args):
        #Menghapus direktori (RMD: 4.1.3)
        if(self.login):
            if(args[0]=="/"):
                new_dir = home + args
            else:
                new_dir = self.aktif + "/" + args
            if(os.path.isdir(new_dir)):
                if not os.listdir(new_dir):
                    os.rmdir(new_dir)
                    return "250 Remove directory operation successful."
                else:
                    return "550 Remove directory operation failed."
            else:
                return "550 Remove directory operation failed."
        else:
            return '530 Please log in with USER and PASS first.\r\n'
        
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
