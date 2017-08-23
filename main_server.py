#!/usr/bin/env python3

"""
Changes from the base class :
- message b"\t" (0x09) now shuts the server down
- the server writes a logfile in ./traffic.log
"""

from server import TCPServer
from sys import argv

logfile = open("./traffic.log","ab")

class MainServer(TCPServer) :

    def do(self,msg,sender):
        info = self.clients[sender]#should be a tuple (hostaddr,port)
        info = info[0]+":"+str(info[1])
        info = info.encode()
        print(info,b":",msg,file=logfile)
        if msg == b"\t" :
            del self
        else :
            TCPServer.do(self,msg,sender)


if __name__ == "__main__" :
    port = int(argv[1])
    main = MainServer(port)
    main.mainloop()
    logfile.close()
