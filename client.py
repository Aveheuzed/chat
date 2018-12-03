#!/usr/bin/env python3

from time import strftime
from socket import socket, gaierror, gethostbyname
from select import select
from threading import Thread
from functools import wraps
import re
import tkinter as tk
from tkinter.constants import *
from tkinter.simpledialog import askstring
from tkinter.messagebox import showerror, showinfo
from tkinter.scrolledtext import ScrolledText

import cipher

VERSION = b"\x01" #to be incremented upon each protocol change
PORT = 1337
SALT = 32 # bytes


class GUIClient :

        def __init__(self, main:tk.Tk, co:socket, login:bytes, seed:bytes):
                self.login = login
                self.main = main
                self.main.title(self.login)
                self.co = co

                self._ciph = cipher.Cipherer(seed)
                self._deciph = cipher.Cipherer(seed)

                self.chatbox = ScrolledText(self.main,state=DISABLED)
                self.inp = tk.Entry(self.main)
                self.inp.bind("<Return>",self.mkpull)

                self.chatbox.pack(side=TOP,fill=BOTH,expand=TRUE)

                self.inp.pack(side=BOTTOM,fill=X)
                self.inp.focus_set()

                self.main_menu = tk.Menu(self.main)
                self.main.configure(menu=self.main_menu)
                self.submenu = tk.Menu(self.main_menu)
                self.main_menu.add_cascade(label="Actions", menu=self.submenu)
                self.submenu.add_command(label="Modifier le mot de passe", command=self.change_password)
                self.submenu.add_separator()
                self.submenu.add_command(label="Créer un utilisateur", command=self.create_user)
                self.submenu.add_command(label="Éteindre le serveur", command=self.shutdown_server)

                self._listen = False

                Thread(target=self.read_daemon).start()

        def exit(self):
                """Properly closes the socket part of the client ; to be called on GUI closure"""
                self._listen= False
                self.co.close()

        def send(self, msg):
            self.co.send(self._ciph.cipher(msg))

        def recv(self, l):
            return self._deciph.decipher(self.co.recv(l))

        def fileno(self):
            return self.co.fileno()

        def mkpull(self,event=None):
                """Sends a message typed by the user"""
                msg = self.inp.get()
                self.inp.delete(0,len(msg))
                msg = msg.strip().encode()
                if len(msg):
                        msg = self.login + b" : " + msg
                        msg = chr(len(msg)).encode() + msg
                        self.send(msg)

        def read_daemon(self):
                """Daemon to read received messages"""
                if self._listen :
                        return
                self._listen = True
                while self._listen :
                        if  not select([self.co], list(), list(), 0)[0] :
                                continue
                        try :
                                l = self.recv(1)
                                assert len(l)
                        except AssertionError :
                                self.exit()
                                break
                        msg = self.recv(ord(l))
                        self.chatbox.configure(state=NORMAL)
                        self.chatbox.insert(END, strftime("%H:%M:%S : "))
                        # we choose to use time.strftime instead of other
                        # builtins formatting functions for they either also
                        # give the date, or floating point seconds
                        self.chatbox.insert(END, msg.decode(errors="replace"))
                        self.chatbox.insert(END, "\n")
                        self.chatbox.configure(state=DISABLED)

        def _special_deco(func):
            @wraps(func)
            def f_(self):
                result = func(self)
                if result == "abort" :
                    return
                flag = self.recv(1)
                if not len(flag) :
                    showinfo("Fatal Error","Une erreur est survenue...")
                    exit(1)
                if ord(flag) :
                    showinfo("Succès !", "L'action a réussi !")
                else :
                    showerror("", "Une erreur est survenue, veuillez réessayer")
                if result == "exit" :
                    exit(0)
            return f_

        @staticmethod
        def askpwd(title_1="Changer son mot de passe",
                   text_1="Nouveau mot de passe : ",
                   title_confirm="Confirmation",
                   text_confirm="Confirmez le mot de passe :",
                   ) :
            while True :
                pwd = askstring(title_1, text_1, show="*")
                if pwd is None :
                    return
                confirm = askstring(title_confirm, text_confirm, show="*")
                if confirm is None :
                    return
                elif confirm == pwd :
                    break
                showerror("", "Les mots de passe ne correspondent pas !")
            return cipher.HASHFUNC(pwd.encode()).digest()


        @_special_deco
        def change_password(self):
            pwdh = self.askpwd()
            if pwdh is None :
                return "abort"
            self.send(b"\x00\x00"+pwdh)

        @_special_deco
        def create_user(self):
            username = askstring("Nouvel utilisateur", "Identifiant du nouvel utilisateur : ")
            if username is None :
                return "abort"
            username = username.encode()
            pwdh = self.askpwd(title_1="Mot de passe",
                               text_1="Mot de passe du nouvel utilisateur")
            if pwdh is None :
                return "abort"
            self.send(b"\x00\x01"+len(username).to_bytes(1,"big")+username+pwdh)

        @_special_deco
        def shutdown_server(self):
            self.send(b"\x00\x02")
            return "exit"


def build_client(main, co):
        # retrieving a valid IP
        while True :
                ip = askstring("Choix du serveur",
                        "Saisissez l'adresse IP/URL du serveur", initialvalue="localhost")
                if ip is None :
                        return 1
                while not ( re.match("[0-9]{1,3}(\\.[0-9]{1,3}){3}", ip) or ip == "localhost" ) :
                        try :
                                ip = gethostbyname(ip)
                        except gaierror :
                            ip = askstring("Choix du serveur",
                                    "Adresse invalide ou inacessible !\nSaisissez l'adresse IP/URL du serveur",
                                    initialvalue="localhost")
                            if ip is None :
                                    return 1
                        else :
                                break


                co.settimeout(0.1)
                try :
                        co.connect((ip, PORT))
                except :
                        continue
                co.send(VERSION)
                if not ord(co.recv(1)) :
                        showerror("Client obsolète",
                                "Téléchargez une version plus récente sur github.com/Aveheuzed/chat")
                        return
                break

        # logging in
        login = askstring("Choix de votre identifiant", "Identifiez-vous :")
        if login is None :
                co.close()
                return
        login = login.encode()
        co.send(len(login).to_bytes(1, "big")+login)
        ans = co.recv(1)
        while not ord(ans) :
                login = askstring("Choix de votre identifiant",
                        "Cet identifiant est invalide. Choisissez-en un autre :")
                if login is None :
                        co.close()
                        return
                login = login.encode()
                co.send(len(login).to_bytes(1, "big")+login)
                ans = co.recv(1)

        # password
        salt = co.recv(SALT)
        password = askstring("Mot de passe", "Mot de passe : ", show="*")
        if password is None :
            co.close()
            return
        # careful : we have to hash it twice, with a salt the 2nd time
        password = cipher.HASHFUNC(password.encode()).digest()
        co.send(cipher.HASHFUNC(password+salt).digest())
        ans = co.recv(1)
        while not ord(ans):
            salt = co.recv(SALT)
            password = askstring("Mot de passe", "Mot de passe : ", show="*")
            if password is None :
                co.close()
                return
            password = cipher.HASHFUNC(password.encode()).digest()
            co.send(cipher.HASHFUNC(password+salt).digest())
            ans = co.recv(1)

        co.settimeout(None)
        # for safety ; setting a timeout causes errors when handling special actions

        # we got everything !
        return GUIClient(main, co, login, seed=password)

if __name__ == '__main__':
    b = build_client(tk.Tk(), socket())
    if not isinstance(b, GUIClient):
            exit(b)
    else :
            b.main.mainloop()
            b.exit()
