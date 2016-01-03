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
    
    def ftp_user(self,arg):
        #Autentikasi (USER dan PASS: 4.1.1)
        self.user = arg
        return '331 Password required for '+arg+'\r\n'

    def ftp_pass(self,arg):
        #Autentikasi (USER dan PASS: 4.1.1)
        if self.user == user and arg == password:
            self.login = True
            return '230 Logged on.\r\n'
        else:
            return '530 Login or password incorrect!\r\n'
    
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
    
    def filestat(self,arg):
        #bagian dari ftp_list
        st=os.stat(arg)
        fullmode='rwxrwxrwx'
        filemode = bin(st.st_mode)[-9:]
        mode=''
        for i in range(9):
            mode += int(filemode[i]) and fullmode[i] or '-'
        d=(os.path.isdir(arg)) and 'd' or '-'
        ftime=time.strftime(' %b %d %H:%M ', time.gmtime(st.st_mtime + 7*3600))
        return d+mode+' 1 owner group '+str(st.st_size)+ftime+os.path.basename(arg)+'\r\n'

    def ftp_list(self,arg = ''):
        #Mendaftar file dan direktori (LIST: 4.1.3)
        if(self.login):
            par = self.aktif
            if arg != '':
                par += '/'+arg
            result = ''
            if os.path.isdir(par):
                listdir = os.listdir(par)
                for fn in listdir:
                    result += self.filestat(par+'/'+fn)
            else:
                result += self.filestat(par)
            return result+'226 Directory send OK.\r\n'
        else:
            return '530 Please log in with USER and PASS first.\r\n'

    def ftp_dele(self,arg):
        #Menghapus file (DELE: 4.1.3)
        if(self.login):
            if(arg[0]=="/"):
                fn = home + args
            else:
                fn = self.aktif + '/' + arg
            if(os.path.isfile(fn)):
                os.remove(fn)
                return "250 File deleted successfully\r\n"
            else:
                return "550 File not found\r\n"
        else:
            return '530 Please log in with USER and PASS first.\r\n'
            
    def ftp_rnfr(self, args):
        if(self.login):
            if(args[0]=="/"):
                self.f = home + args
            else:
                self.f = self.aktif + '/' + args
            if(os.path.isfile(self.f)):
                return "350 Ready for RNTO.\r\n"
            else:
                self.f = ""
                return "550 RNFR command failed\r\n"
        else:
            return '530 Please log in with USER and PASS first.\r\n'

    def ftp_rnto(self, args):
        if(self.login):
            if(self.f==""):
                return "RNFR required first.\r\n"
            else:
                new_f = ""
                if(args[0]=="/"):
                    new_f = home + args
                else:
                    new_f = self.aktif + '/' + args
                os.rename(self.f,new_f)
                self.f == ""
                return "250 Rename succesful.\r\n"
        else:
            return '530 Please log in with USER and PASS first.\r\n'
            
    def ftp_stor(self,arg):
        if(self.login):
            fn = self.aktif+'/'+arg
            if(os.path.isfile(fn)):
                return "553 File already exist\r\n"
            else:
                data=''
                total=''
                i=0
                iki=sock.recv(1024)
                size=int(iki.split('/r/n/r/n')[0])
                total=iki.split('/r/n/r/n')[1]
                size=size-len(iki.split('/r/n/r/n')[1])
                while i < size:
                    data = sock.recv(1024)
                    total=total+data
                    i=i+1024
                f = open(fn,'wb')
                f.write(total)
                f.close()
                return '200 File' + arg.split('/')[-1:] + 'uploaded.\r\n'
        else:
             return '530 Please log in with USER and PASS first.\r\n'

    def ftp_retr(self,arg):
        if(self.login):
            fn = self.aktif+'/'+arg
            if(os.path.isfile(fn)):
                f = open(filename,'rb')
                f.seek(0,2)
                size = f.tell()
                data = str(size)+'/r/n/r/n'
                f.seek(0)
                data = data+f.read()
                sock.send(data)
                f.close()
                return '200 File' + arg.split('/')[-1:] + 'downloaded.\r\n'
            else:
                return "550 File not found\r\n"
        else:
             return '530 Please log in with USER and PASS first.\r\n'
    
    def ftp_quit(self):
        #Keluar aplikasi (QUIT: 4.1.1)
        self.login = False
        return "221 Goodbye."

    def ftp_help():
        #HELP: 4.1.3
        msg = "214-The following commands are recognized.\n"
        msg += "ABOR ACCT ALLO APPE CDUP CWD  DELE EPRT EPSV FEAT HELP LIST MDTM MKD\n"
        msg += " MODE NLST NOOP OPTS PASS PASV PORT PWD  QUIT REIN REST RETR RMD  RNFR\n"
        msg += " RNTO SITE SIZE SMNT STAT STOR STOU STRU SYST TYPE USER XCUP XCWD XMKD\n"
        msg += " XPWD XRMD\n"
        msg += "214 help OK."
        return msg
    
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
                if(command.split()[0].strip().upper() == "LIST"):
                    sock.send(ftp.ftp_list().strip())
                elif(command.split()[0].strip().upper() == "PWD"):
                    sock.send(ftp.ftp_pwd().strip())
                elif(command.split()[0].strip().upper() == "CWD"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_cwd(param).strip())
                elif(command.split()[0].strip().upper() == "USER"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_user(param).strip())
                elif(command.split()[0].strip().upper() == "PASS"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_pass(param).strip())
                elif(command.split()[0].strip().upper() == "MKD"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_mkd(param).strip())
                elif(command.split()[0].strip().upper() == "RMD"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_rmd(param).strip())
                elif(command.split()[0].strip().upper() == "DELE"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_dele(param).strip())
                elif(command.split()[0].strip().upper() == "RNFR"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_rnfr(param).strip())
                elif(command.split()[0].strip().upper() == "RNTO"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_rnto(param).strip())
                elif(command.split()[0].strip().upper() == "STOR"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_stor(param).strip())
                elif(command.split()[0].strip().upper() == "RETR"):
                    param = command.split()[1].strip()
                    sock.send(ftp.ftp_retr(param).strip())
                elif(command.split()[0].strip().upper() == "QUIT"):
                    sock.send(ftp.ftp_quit().strip())
                elif(command.split()[0].strip().upper() == "HELP"):
                    sock.send(ftp.ftp_help().strip())
                else:
                    sock.send("500 Unknown command.")

except KeyboardInterrupt:
    server_socket.shutdown()
    server_socket.close()
    sys.exit(0)
