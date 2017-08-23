from socket import socket
from select import select

class TCPClient :
    """This class impements the simplest TCP client.
To improve it, just redefine the self.build_msg and self.parse_msg methods."""

    def __init__(self,port,hote="localhost"):
        """Instance attributes :
- self.hote (str) : IP adress of the server
- self.port (int) : -
- self.co (socket) : the main connection
"""
        self.hote = hote
        self.port = port

        self.co = socket()
        self.co.connect((self.hote,self.port))

    def __repr__(self):
        return "TCP client of {}:{}".format(self.hote,self.port)

    def __del__(self):
        self.co.close()

    def recv(self,x=1024):
        if len(select([self.co,],list(),list(),0)[0]) :
            return self.parse_msg(self.co.recv(x))

    def send(self,msg):
        self.co.send(self.build_msg(msg))
        return len(msg)

    def build_msg(self,msg):
        """message formatter for sending, called by send (internal method)"""
        return msg

    def parse_msg(self,msg):
        """message parser for receiving, called by recv (internal method)"""
        return msg
