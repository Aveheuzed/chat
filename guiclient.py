#!/usr/bin/env python3

from client import TCPClient as Nw
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from threading import Thread

class Client(Nw,Thread):

        def __init__(self,textbox):
                Thread.__init__(self)
                Nw.__init__(1337,"255.255.255.255")
                self.textbox = textbox
                self.r = True

        def run(self):
                while self.r :
                        r = self.recv()
                        if r is not None :
                                self.textbox.insert("END",r)
                del self

main = tk.Tk()

# asking for a username
t = tk.Toplevel()
tk.Label(t,text="Choose an username : ").pack(side="left",fill="x")
e = tk.Entry(t)
e.pack(side="right",fill="x")
tk.Button(t,text="OK",command=t.destroy).pack(side="bottom")
t.mainloop()

# retrieving it
username = e.get() + " : "
username = username.encode()

# buildong the chat window
chatbox = ScrolledText(main,state="disabled")
chatbox.pack(side="top",fill="x",expand=True)

inp = Tk.Entry(main)
inp.pack(side="bottom",fill="x")

# network side...
client = Client(chatbox)

def _(ev):
        client.r = not client.r
        # this stops the thread
main.bind("<Destroy>", _)

# this function is called to send a message the user just typed
def mkpull(entry,nw,name):
        def f(*args,**kwargs):
                nw.send(username+entry.get().encode())
                entry.delete(0,"END")
        return f

inp.bind("<Return>",mkpull(entry,client,username))


client.start()
main.mainloop()
client.join()
