#!/usr/bin/env python3

from sys import argv

# common
# client

from time import strftime
from socket import socket, gaierror, gethostbyname
from select import select
from threading import Thread

import tkinter as tk
from tkinter.constants import *
from tkinter.simpledialog import askstring
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText
import re

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


def build_client(main, co):
        # retrieving a valid IP
        while True :
                ip = askstring("Choix du serveur", "Saisissez l'adresse IP/URL du serveur", initialvalue="localhost")
                if ip is None :
                        return 1
                while not ( re.match("[0-9]{1,3}(\\.[0-9]{1,3}){3}", ip) or ip == "localhost" ) :
                        try :
                                ip = gethostbyname(ip)
                        except gaierror :
                            ip = askstring("Choix du serveur", "Adresse invalide ou inacessible !\nSaisissez l'adresse IP/URL du serveur", initialvalue="localhost")
                            if ip is None :
                                    return 1
                        else :
                                break
                                

                co.settimeout(0.1)
                try :
                        co.connect((ip, PORT))
                except :
                        continue
                else :
                        co.send(VERSION)
                        if not ord(co.recv(1)) :
                                showerror("Client obsolète", "Téléchargez une version plus récente sur github.com/Aveheuzed/chat")
                                return 2
                        break # should be alone in the "else" block ("flat is better than nested")

        # logging in
        login = askstring("Choix de votre identifiant", "Identifiez-vous :")
        if login is None :
                co.close()
                return 1
        login = login.encode()
        co.send(len(login).to_bytes(1, "big") +login)
        ans = co.recv(1)
        while not ord(ans) :
                login = askstring("Choix de votre identifiant", "Cet identifiant est déjà pris. Choisissez-en un autre :")
                if login is None :
                        co.close()
                        return 1
                login = login.encode()
                co.send(chr(len(login)).encode()+login)
                ans = co.recv(1)

        # we got everything !
        return GUIClient(main, co, login)


class GUIClient :

        def __init__(self, main, co, login):
                self.login = login
                self.main = main
                self.main.title(self.login)
                self.co = co

                self.chatbox = ScrolledText(self.main,state=DISABLED)
                self.inp = tk.Entry(self.main)
                self.inp.bind("<Return>",self.mkpull)

                self.chatbox.pack(side=TOP,fill=BOTH,expand=TRUE)

                self.inp.pack(side=BOTTOM,fill=X)
                self.inp.focus_set()

                self._listen = False

                Thread(target=self.read_daemon).start()

                self.main.bind("<Destroy>", self._exit)

        def _exit(self, event=None):
                """Properly closes the socket part of the client ; to be called on GUI closure"""
                self._listen= False
                self.co.close()

        def mkpull(self,event=None):
                msg = self.inp.get()
                self.inp.delete(0,len(msg))
                msg = msg.strip().encode()
                if len(msg):
                        msg = chr(len(msg)).encode() + msg
                        self.co.send(msg)

        def read_daemon(self):
                if self._listen :
                        return
                self._listen = True
                while self._listen :
                        if  not select([self.co], list(), list(), 0)[0] :
                                continue
                        try :
                                l = self.co.recv(1)
                                assert len(l)
                        except :
                                self._exit()
                                break
                        msg = self.co.recv(ord(l))
                        self.chatbox.configure(state=NORMAL)
                        self.chatbox.insert(END, strftime("%d/%m/%Y %H:%M:%S : "))
                        self.chatbox.insert(END, msg.decode())
                        self.chatbox.insert(END, "\n")
                        self.chatbox.configure(state=DISABLED)

if __name__ == '__main__':
        if len(argv) > 1 :
                if argv[1] == "-s" :
                        Server().start()
                else :
                        exit(3)
        else :
                b = build_client(tk.Tk(), socket())
                if isinstance(b,int):
                        exit(b)
                else :
                        b.main.mainloop()
