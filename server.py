#!/usr/bin/env python3
from socket import socket
from select import select

class TCPServer :
    """This class implements the simplest TCP server, just sending back each received segment to each connected client.
To improve this server, just redefine the self.do method."""

    def __init__(self,port,msg_len=1024):
        """Instance attributes :
- self.port (int) : -
- self.msg_len (int) : the maximale length for a single message
- self.co (socket) : the main connection on witch to listen
- self.clients (dict) : of the form {client : info_about_it}
"""
        self.port = port
        self.msg_len = msg_len

        self.co = socket()
        self.co.bind(('',self.port))
        self.clients = dict()# client : info_client
        self.mainloop_marker = False # set to Tue when/while mainloop is running

    def __repr__(self):
        return "TCP server on port {}".format(self.port)

    def __del__(self):
        """Shuts the server down."""
        self.mainloop_marker = False
        # for c in self.clients :
        #     c.close()
        # self.co.close()

    def mainloop(self):
        """/!\\ Warning : this function will launch an infinite loop, unless
you break it with ^C or by deleting self (in the self.do method)
    In that loop, the server will be fully available."""
        self.co.listen()
        self.mainloop_marker = True
        while self.mainloop_marker :
                asked = select([self.co,],list(),list(),0)[0]

                for co in asked :
                        client,info = co.accept()
                        self.clients[client] = info

                if len(self.clients):
                        to_read = select(self.clients.keys(),list(),list(),0)[0]
                        for client in to_read :
                            msg = client.recv(self.msg_len)
                            self.do(msg,client)

        for c in self.clients :
            c.close()
        self.co.close()


    def do(self,msg,sender):
        """This method is called by mainloop for each received segment."""
        brokenpipes = set()
        for c in self.clients.keys() :
            try :
                c.send(msg)
            except BrokenPipeError :
                brokenpipes.add(c)
        for br in brokenpipes :
            del self.clients[br]

if __name__ == "__main__" :
    from sys import argv
    p = int(argv[1])
    s = TCPServer(p)
    s.mainloop()
