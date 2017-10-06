#!/usr/bin/env python3

from client import TCPClient as Nw
import tkinter as tk
from tkinter.simpledialog import askstring
from tkinter.scrolledtext import ScrolledText
from threading import Thread

class Client(Nw,Thread):

        def __init__(self,textbox):
                Thread.__init__(self)
                Nw.__init__(self,1337,"127.0.0.1")
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

username = askstring("Choisissez un nom", "Identifiez-vous :").encode() + b" : "

# buildong the chat window
chatbox = ScrolledText(main,state="disabled")
chatbox.pack(side="top",fill="x",expand=True)

inp = tk.Entry(main)
inp.pack(side="bottom",fill="x")
inp.focus_set()

# network side...
client = Client(chatbox)

def _(ev):
        client.r = not client.r
        # this stops the thread
main.bind("<Destroy>", _)

# this function is called to send a message the user just typed
def mkpull(entry,nw,name):
        def f(*args,**kwargs):
                msg = entry.get().encode()
                nw.send(username+msg)
                entry.delete(0,len(msg))
        return f

inp.bind("<Return>",mkpull(inp,client,username))


client.start()
main.mainloop()
client.join()
