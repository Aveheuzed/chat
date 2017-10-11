#!/usr/bin/env python3

"""
Changes from the base class :
- message b"\t" (0x09) now shuts the server down
- the server writes a logfile in ./traffic.log
"""

from server import TCPServer
from sys import argv
from time import strftime

class MainServer(TCPServer) :

        def __init__(self,port,msg_len=1024,logfile="./traffic.log") :
                super().__init__(port,msg_len)
                self.logfile = open(logfile,"at")
                self.log_append("***Server wakes up***")

        def __del__(self):
                self.log_append("***Server shut down***")
                self.logfile.close()
                super().__del__()

        def do(self,msg,sender):
                if not len(msg) :
                        return
                info = self.clients[sender]#should be a tuple (hostaddr,port)
                info = info[0]+":"+str(info[1])
                self.log_append(info,":",msg.decode())
                if msg == b"\t" :
                    self.__del__()
                else :
                    TCPServer.do(self,msg,sender)

        def log_append(self, msg):
                print(time.strftime("%d/%m/%Y %H:%M:%S"), msg, sep=" / ", file=self.logfile)


port = 1337
main = MainServer(port)
main.mainloop()
