#!/usr/bin/env python3

from client import TCPClient
from sys import argv
from time import strftime
from threading import Thread

class MsgReader(Thread):

    def run(self):
        global typed
        while True:
            typed = input()

class Client(TCPClient) :

    def build_msg(self,msg):
        return (strftime("%H:%M:%S")+" <"+username+"> : ").encode()+msg+b"\n"

if __name__ == "__main__" :
    username = argv[1]
    ip,_,port = argv[2].partition(":")
    port = int(port) ; del _


    main = Client(port,ip)
    reader = MsgReader()
    reader.start()

    while True :
        typed = str()
        m = main.recv()
        if m is not None :
            print(m.decode(),end="")
        if typed :
            if typed.startswith("/"):#put various commands here.
                if typed == "/leave" :
                    del reader
                    break
                elif typed == "/kill" :
                    main.send(b"\x09")
                    del main
                    break
            else :
                main.send(typed.strip().encode()[:1024])
