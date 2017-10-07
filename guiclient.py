#!/usr/bin/env python3

from client import TCPClient as Nw
import tkinter as tk
from tkinter.simpledialog import askstring
from tkinter.scrolledtext import ScrolledText
from threading import Thread
from sys import argv
import re

class Client(Nw,Thread):

        def __init__(self,textbox, port, ip):
                Thread.__init__(self)
                Nw.__init__(self,port, ip)
                self.textbox = textbox
                self.r = True

        def run(self):
                while self.r :
                        r = self.recv()
                        if r is not None :
                                r = r.decode()
                                self.textbox["state"] = "normal"
                                self.textbox.insert("end",r+"\n")
                                self.textbox["state"] = "disabled"
                del self


main = tk.Tk()


if len(argv) > 1 :
        ip = argv[1]
else :
        ip = askstring("Choix du serveur", "Saisissez l'adresse IP du serveur", initialvalue="localhost")

while not re.match("[0-9]{1,3}(\\.[0-9]{1,3}){3}", ip) or ip == "localhost" :
        ip = askstring("Choix du serveur", "Adresse invalide !\nSaisissez l'adresse IP du serveur", default="localhost")

port = 1337

username = askstring("Choisissez un nom", "Identifiez-vous :").encode() + b" : "

# buildong the chat window
chatbox = ScrolledText(main,state="disabled")
chatbox.pack(side="top",fill="x",expand=True)

inp = tk.Entry(main)
inp.pack(side="bottom",fill="x")
inp.focus_set()

# network side...
client = Client(chatbox, port, ip)

def _(ev):
        client.r = not client.r
        # this stops the thread
main.bind("<Destroy>", _)

# this function is called to send a message the user just typed
def mkpull(entry,nw,name):
        def f(*args,**kwargs):
                msg = entry.get()
                entry.delete(0,len(msg))
                msg = msg.strip().encode()
                if len(msg):
                        nw.send(username+msg)
        return f

inp.bind("<Return>",mkpull(inp,client,username))


client.start()
main.mainloop()
client.join()
