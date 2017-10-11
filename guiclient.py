#!/usr/bin/env python3

from client import TCPClient as Nw
import tkinter as tk
from tkinter.simpledialog import askstring
from tkinter.scrolledtext import ScrolledText
from threading import Thread
from sys import argv
import re
from time import strftime

class Client(Nw,Thread):

        def __init__(self,textbox, port, ip, username):
                Thread.__init__(self)
                Nw.__init__(self,port, ip)
                self.username = username
                self.textbox = textbox
                self.r = True

        def build_msg(self, msg) :
                return self.username + b" : "+msg

        def parse_msg(self,msg):
                msg = msg.decode()
                return strftime("%H:%S:%M")+" / "+msg+"\n"

        def run(self):
                while self.r :
                        r = self.recv()
                        if r is not None :
                                self.textbox["state"] = "normal"
                                self.textbox.insert("end",r)
                                self.textbox["state"] = "disabled"
                del self


port = 1337
main = tk.Tk()

chatbox = ScrolledText(main,state="disabled")
inp = tk.Entry(main)

username = askstring("Choisissez un nom", "Identifiez-vous :").encode()

if len(argv) > 1 :
        ip = argv[1]
else :
        ip = askstring("Choix du serveur", "Saisissez l'adresse IP du serveur", initialvalue="localhost")

if ip is None :
        main.destroy()
        exit(0)

# asking for the server IP
while True :
        while not re.match("[0-9]{1,3}(\\.[0-9]{1,3}){3}", ip) and ip != "localhost" :
                ip = askstring("Choix du serveur", "Adresse invalide ou inacessible !\nSaisissez l'adresse IP du serveur", default="localhost")
                if ip is None :
                        main.destroy()
                        exit(0)
        try :
                client = Client(chatbox, port, ip, username)
        except :
                continue
        else :
                break

client.co.send(username+b" logged in.")
# we have to use client.co.send to avoid the client's formatting

# buildong the chat window
chatbox.pack(side="top",fill="x",expand=True)

inp.pack(side="bottom",fill="x")
inp.focus_set()

def _(ev):
        client.r = not client.r
        # this stops the thread
main.bind("<Destroy>", _)

# this function is called to send a message the user just typed
def mkpull(entry,nw):
        def f(*args,**kwargs):
                msg = entry.get()
                entry.delete(0,len(msg))
                msg = msg.strip().encode()
                if len(msg):
                        nw.send(msg)
        return f

inp.bind("<Return>",mkpull(inp,client))


client.start()
main.mainloop()
client.join()
