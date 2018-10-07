#!/usr/bin/env python3

from time import strftime
from socket import socket, gaierror, gethostbyname
from select import select
from threading import Thread
import re
import tkinter as tk
from tkinter.constants import *
from tkinter.simpledialog import askstring
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText

VERSION = b"\x00" #to be incremented upon each protocol change
PORT = 1337

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

if __name__ == '__main__':
    b = build_client(tk.Tk(), socket())
    if isinstance(b,int):
            exit(b)
    else :
            b.main.mainloop()