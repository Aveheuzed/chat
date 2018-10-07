#!/usr/bin/env python3

from socket import socket
from select import select
from threading import Thread
from time import strftime

VERSION = b"\x00" #to be incremented upon each protocol change
PORT = 1337


class Server(Thread) :

        def __init__(self,port=PORT, logfile="./logfile.log"):
                super().__init__()

                self.port = port
                self.logfile = open(logfile, "ab")

                self.co = socket()
                self.co.bind(("", self.port))

                self.clients = set()
                self.names = set()

        def __del__(self):
                self.co.close()

        def run(self):
                self.co.listen(5)
                while True :
                        asked = select([self.co, ], list(), list(), 0)[0]
                        for co in asked :
                                client, info = co.accept()
                                Thread(target=self.handle_client, args=(client,)).start()

        def write_log(self, message):
                self.logfile.write(strftime("%d/%m/%Y %H:%M:%S : ").encode())
                self.logfile.write(message+b"\n")

        def sendall(self, msg):
                """Sends msg to each connected client"""
                for client in self.clients :
                        try :
                                client.send(msg)
                        except :
                                # the broken thread will manage the removings by itself
                                continue

        def handle_client(self, myclient):
                ver = myclient.recv(1)
                if ver != VERSION :
                        client.send(b"\x00")
                        client.close()
                        del self.clients[client]
                else :
                        myclient.send(b"\x01")
                        l = ord(myclient.recv(1)) # the message is that value long
                        username = myclient.recv(l)
                        while username in self.names :
                                myclient.send(b"\x00")
                                l = ord(myclient.recv(1))
                                username = myclient.recv(l)
                        self.names.add(username)
                        myclient.send(b"\x01")
                        self.clients.add(myclient)

                        self.write_log(repr(myclient.getsockname()).encode()+b" logged in as "+username)
                        msg = username + b" logged in"
                        msg = len(msg).to_bytes(1,"big") + msg
                        self.sendall(msg)

                        while True :
                                try :
                                        l = myclient.recv(1)
                                except :
                                        break
                                if not len(l):
                                        break
                                else :
                                        l = ord(l)
                                        msg = myclient.recv(l)
                                        msg = username + b" : " + msg
                                        self.write_log(msg)
                                        l = len(msg).to_bytes(1,"big")
                                        msg = l+msg
                                        self.sendall(msg)
                        self.clients.remove(myclient)
                        myclient.close()
                        msg = username + b" logged out"
                        self.write_log(msg)
                        msg = len(msg).to_bytes(1,"big") + msg
                        self.sendall(msg)
                        self.names.remove(username)

if __name__ == '__main__':
    Server().start()
