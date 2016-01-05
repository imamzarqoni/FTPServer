import socket, select, time, sys, os, threading

msg = ""
home = 'home' #ftp directory
user = 'progjar' #username
password = '123' #password

class FTPclient(threading.Thread):
    def __init__(self,sock):
        threading.Thread.__init__(self)
        self.aktif = home #direktori aktif
        self.user = '' #username input
        self.login = False #status login
        self.sock = sock
        self.f = ''

    def run(self):
        self.sock.send('220 FTPserver.\r\n')
        while True:
            data = self.sock.recv(1024)
            if data:
                split = data.split()
                if hasattr(self,split[0].strip().upper()):
                    command = getattr(self,split[0].strip().upper())
                    result = ''
                    if(len(split) > 1):
                        arg = ' '.join(split[1:])
                        result = command(arg)
                    else:
                        result = command()
                    self.sock.send(result)
                else:
                    self.sock.send('202 Command not implemented.\r\n')
            else:
                self.sock.close()
                break
    
    def USER(self,arg):
        #Autentikasi (USER dan PASS: 4.1.1)
        self.user = arg
        return '331 Password required for '+arg+'\r\n'

    def PASS(self,arg):
        #Autentikasi (USER dan PASS: 4.1.1)
        if self.user == user and arg == password:
            self.login = True
            return '230 Logged on.\r\n'
        else:
            return '530 Login or password incorrect!\r\n'
    
    def PWD(self):
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

    def CWD(self,args):
        #Mengubah direktori aktif (CWD: 4.1.1)
        if(self.login):
            msg = "250 Directory successfully changed.\r\n"
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
                        return "550 Failed to change directory.\r\n"
                else:
                    if(args[0]=="/"):
                        self.aktif = home + args
                    else:
                        self.aktif = self.aktif + "/" + args
                    print self.aktif
                    if(os.path.isdir(self.aktif)):
                        return msg
                    else:
                        return "550 Failed to change directory.\r\n"
        else:
            return '530 Please log in with USER and PASS first.\r\n'

    def MKD(self,args):
        #Membuat direktori (MKD: 4.1.3)
        if(self.login):
            if(args[0]=="/"):
                new_dir = home + args
            else:
                new_dir = self.aktif + "/" + args
            if(os.path.isdir(new_dir)):
                return "550 Create directory operation failed.\r\n"
            else:
                os.makedirs(new_dir)
                dirs = os.path.relpath(new_dir,home)
                if dirs == ".":
                    dirs = "/"
                else:
                    dirs = "/" + dirs
                msg = "257 \"" + dirs + "\" created.\r\n"
                return msg
        else:
            return '530 Please log in with USER and PASS first.\r\n'
            
    def RMD(self,args):
        #Menghapus direktori (RMD: 4.1.3)
        if(self.login):
            if(args[0]=="/"):
                new_dir = home + args
            else:
                new_dir = self.aktif + "/" + args
            if(os.path.isdir(new_dir)):
                if not os.listdir(new_dir):
                    os.rmdir(new_dir)
                    return "250 Remove directory operation successful.\r\n"
                else:
                    return "550 Remove directory operation failed.\r\n"
            else:
                return "550 Remove directory operation failed.\r\n"
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

    def LIST(self,arg = ''):
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
                result += '226 Directory send OK.\r\n'
            elif os.path.isfile(par):
                result += self.filestat(par)
                result += '226 Directory send OK.\r\n'
            else:
                result += '500 Directory or file not found.\r\n'
            return result
        else:
            return '530 Please log in with USER and PASS first.\r\n'

    def DELE(self,arg):
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
            
    def RNFR(self, args):
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

    def RNTO(self, args):
        if(self.login):
            if(self.f==""):
                return "550 RNFR required first.\r\n"
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
            
    def STOR(self,arg):
        if(self.login):
            fn = self.aktif+'/'+arg
            if(os.path.isfile(fn)):
                return "553 File already exist\r\n"
            else:
                i=0
                iki=self.sock.recv(1024)
                iki=iki.split('/r/n/r/n')
                size=int(iki[0])
                total='/r/n/r/n'.join(iki[1:])
                size=size-len(total)
                while i < size:
                    data = self.sock.recv(1024)
                    total=total+data
                    i=i+1024
                f = open(fn,'wb')
                f.write(total)
                f.close()
                return '200 File ' + arg.split('/')[-1] + ' uploaded.\r\n'
        else:
             return '530 Please log in with USER and PASS first.\r\n'

    def RETR(self,arg):
        if(self.login):
            fn = self.aktif+'/'+arg
            if(os.path.isfile(fn)):
                size = os.stat(fn).st_size
                f = open(fn,'rb')
                data = str(size)+'/r/n/r/n'
                data = data+f.read()
                self.sock.send(data)
                f.close()
                self.sock.recv(1024)
                return '200 File ' + arg.split('/')[-1] + ' downloaded.\r\n'
            else:
                return "500 File not found\r\n"
        else:
             return '530 Please log in with USER and PASS first.\r\n'
    
    def QUIT(self):
        #Keluar aplikasi (QUIT: 4.1.1)
        self.login = False
        return "221 Goodbye.\r\n"

    def HELP(self):
        #HELP: 4.1.3
        msg = "214-The following commands are recognized.\n"
        msg += "ABOR ACCT ALLO APPE CDUP CWD  DELE EPRT EPSV FEAT HELP LIST MDTM MKD\n"
        msg += " MODE NLST NOOP OPTS PASS PASV PORT PWD  QUIT REIN REST RETR RMD  RNFR\n"
        msg += " RNTO SITE SIZE SMNT STAT STOR STOU STRU SYST TYPE USER XCUP XCWD XMKD\n"
        msg += " XPWD XRMD\n"
        msg += "214 help OK.\r\n"
        return msg


class FTPserver(threading.Thread):
    def run(self):        
        server_address = (socket.gethostname(), 5000)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(server_address)
        server_socket.listen(10)

        input_socket = [server_socket]
        threads = []

        try:
            while True:
                read_ready, write_ready, exception = select.select(input_socket, [], [])
                
                for sock in read_ready:
                    if sock == server_socket:
                        client_socket, client_address = server_socket.accept()
			print "connected :", client_socket.getpeername()
                        t = FTPclient(client_socket)
                        t.start()
                        threads.append(t)
        
        except KeyboardInterrupt:
            server_socket.shutdown()
            server_socket.close()
            sys.exit(0)

ftp = FTPserver()
ftp.start()
