#!/usr/bin/env python3

import socket, sys, re

s = socket.socket()
if len(sys.argv) > 1 :
        ip = sys.argv[1]
else :
        ip = input("Server IP adress : ")
if not ip :
        exit()
while not re.match("[0-9]{1,3}(\\.[0-9]{1,3}){3}", ip) and ip != "localhost" :
        ip = input("Bad adress.\nServer IP adress : ")
        if not ip :
                exit()
port = 1337
s.connect((ip,port))
s.send(b"\t")
s.close()
print("Server shut down.")
