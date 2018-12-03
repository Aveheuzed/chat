#!/usr/bin/env python3

from socket import socket
from select import select
from threading import Thread
from pathlib import Path
from functools import wraps
from datetime import datetime
import pickle
import secrets
import getpass

import cipher

VERSION = b"\x01" #to be incremented upon each protocol change
PORT = 1337
DB_PATH = Path(__file__).parent/"pwd_db.bin"
SALT = 32 # bytes


class RestrictedUnpickler(pickle.Unpickler) :

    """Unpickling class that forbides non-built-in elements ;
    shall be unsed for the PasswordMGR, witch will unpickle only dicts and bytes
    """

    def find_class(self,module, name) :
        raise pickle.UnpicklingError(
            "{}.{} : not allowed at unpickling !".format(module, name))

    @staticmethod
    def safe_load(fh):
        return __class__(fh).load()


class PasswordMGR(dict) :

    __slots__ = "_path" # the only attribute of this class' instances is "_path"

    def __new__(cls, _path:Path=DB_PATH) :
        # is this method useful at all ?
        return super().__new__(cls)

    def __init__(self, _path:Path=DB_PATH):
        self._path = _path
        if _path.exists() :
            self.update(RestrictedUnpickler.safe_load(_path.open("rb")))
        else :
            self._path.touch()

    def __save_state(func):
        """Decorator that saves self's state after the call.
        The decorated function must return nothing."""
        @wraps(func)
        def f_(self, *args, **kwargs):
            func(self, *args, **kwargs)
            pickle.dump(obj=dict(self), file=self._path.open("wb"))
        return f_

    __setitem__ = __save_state(dict.__setitem__)
    __delitem__ = __save_state(dict.__delitem__)

    path = property(lambda self:self._path)


class ClientHandler :

    def __init__(self, server, co, username:bytes, seed) :
        self.server = server
        self.co = co
        self.login = username
        self._ciph = cipher.Cipherer(seed)
        self._deciph = cipher.Cipherer(seed)

    def __del__(self):
        self.co.close()

    def send(self, msg):
        # do we want to cipher msg's len ?
        # now we do
        self.co.send(self._ciph.cipher(msg))

    def recv(self, l):
        """Reads and deciphers a message"""
        return self._deciph.decipher(self.co.recv(l))

    def _refuse(self, action):
        self.send(b"\x00")
        self.server.write_log(f"Client {self.co.getpeername()} tries to perform an un[known|authorized] action : {action}")

    def read_message(self):
        """Proceeds the client's request - either chatting or a special request
        Returns the message to be broadcasted, if any (prefixed with its length), or None"""
        l = self.recv(1)
        if not l : # -> (l of length 0) <- != (l=b"\x00")
            return
        ord_l = ord(l)
        if ord_l : # plain message, just text
            msg = self.recv(ord_l)
            return l + msg
            # return self.recv(ord(l))
        else :
            action = ord(self.recv(1))
            # nr / action
            # 0 <password hash> : modifies self's password <= sole unprivileged action
            # 1 <l> <username> <password hash> : creates an account
            # 2 : shuts the server down
            if not action :
                self.server.pwdmgr[self.login] = self.recv(len(self.server.pwdmgr[self.login]))
                self.send(b"\x01")
            # note about the structure for privileged actions :
            # we do everything as if it were allowed until actually
            # doing anything in order not to display any sensitive data
            # (anything we don't read will be treated as a plain chat message)
            elif action == 1 :
                l = self.recv(1)
                username = self.recv(l)
                pwdh = self.recv(len(self.server.pwdmgr[self.login]))
                if self.login != b"admin" :
                    self._refuse(action)
                else :
                    self.server.pwdmgr[username] = pwdh
                    self.send(b"\x01")
            elif action == 2 :
                if self.login != b"admin" :
                    self._refuse(action)
                else :
                    self.send(b"\x01")
                    # here, we begin with that,
                    # cuz the server is gonna be shut down
                    self.server.stop()
            else :
                self._refuse(action)
            # about len(self.server.pwdmgr[self.login]) :
            # this is the best method I've found to get the paswword hash's length
            # it does not depend on the hash algorithm (HASHFUNC)
            # and it is not hard-coded.

    def fileno(self):
        return self.co.fileno()

    def getpeername(self):
        return self.co.getpeername()

    # make the class transpatent with a __getattribute__ ?
    # i.e. automatically redirects method calls to self.co


class Server(Thread) :

        def __init__(self, port=PORT, logfile="./logfile.log", pwd_db_path=DB_PATH):
                """Logfile may be str ; pwd_db_path must be Path"""
                super().__init__()

                self.logfile = open(logfile, "a")
                self.write_log(f"Initializing with paramters {locals()} ...")
                self.port = port
                self.pwdmgr = PasswordMGR(pwd_db_path)
                if b"admin" in self.pwdmgr.keys() :
                    self.write_log("\tAdmin credentials found, skipping admin registration.")
                else :
                    self.write_log("\tAdmin credentials not found, registering one...")
                    print("Master login : admin")
                    pwd1 = True ; pwd2 = not pwd1
                    while pwd1 != pwd2 :
                        pwd1 = getpass.getpass("Define master password : ")
                        pwd2 = getpass.getpass("Confirm master password : ")
                    self.pwdmgr[b"admin"] = cipher.HASHFUNC(pwd1.encode()).digest()
                    self.write_log("\tDone.")

                self.running = True

                self.co = socket()
                self.co.bind(("", self.port))

                self.clients = set()
                self.names = set()

                self.write_log("Done.")

        def run(self):
                self.write_log("Entering mainloop...")
                self.co.listen(5)
                while self.running :
                        asked = select([self.co, ], list(), list(), 0)[0]
                        for co in asked :
                                client, info = co.accept()
                                self.write_log(f"\tNew client from {info}")
                                Thread(target=self.handle_client, args=(client,)).start()
                        for cco in select(self.clients, list(), list(), 0)[0] :
                            self.sendall(cco.read_message())
                        else : #this block is always executed (cleanup step)
                            self.sendall(b"")
                            # no effect on connected clients ;
                            # raises an exception (catched) for broken pipes
                self.write_log("Exiting mainloop.")
                self.co.close()
                for cco in self.clients :
                    cco.co.close() # Instances of ClientHandler there

        def write_log(self, message:str):
                self.logfile.write(format(datetime.now())+" : ")
                self.logfile.write(message+"\n")
                self.logfile.flush()

        def sendall(self, msg):
                """Sends msg to each connected client ;
                do not forget to prefix it with its length !"""
                # # don't uncomment these lines ;
                # # sending b"" is useful to seek broen pipes
                # if not msg :
                #     return
                rm = set()
                for client in self.clients :
                        try :
                                client.send(msg)
                        except :
                                rm.add(client)
                                continue

                for client in rm :
                    self.write_log(f"\tClient {client.getpeername()} left")
                    self.clients.remove(client)
                    self.names.remove(client.login)
                for client in rm :
                    msg = client.login + " s'est déconnecté.".encode()
                    self.sendall(len(msg).to_bytes(1, "big")+msg) # may lead to infinite recursion !!

        def handle_client(self, myclient):
                # version check
                ver = myclient.recv(1)
                if ver != VERSION :
                        myclient.send(b"\x00")
                        myclient.close()
                        return
                else :
                        myclient.send(b"\x01")
                # username
                l = ord(myclient.recv(1))
                username = myclient.recv(l)
                while username not in self.pwdmgr or username in self.names :
                        myclient.send(b"\x00")
                        l = ord(myclient.recv(1))
                        username = myclient.recv(l)
                self.names.add(username)
                myclient.send(b"\x01")
                # password
                while True :
                    salt = secrets.token_bytes(SALT)
                    myclient.send(salt)
                    expected = cipher.HASHFUNC(self.pwdmgr[username] + salt).digest()
                    try :
                        gotten = myclient.recv(len(expected))
                    except :
                        myclient.close()
                        self.names.remove(username)
                        return
                    if secrets.compare_digest(expected, gotten) :
                        myclient.send(b"\x01")
                        break
                    else :
                        myclient.send(b"\x00")

                self.clients.add(ClientHandler(self, myclient, username, self.pwdmgr[username]))

                self.write_log(f"\tClient {myclient.getpeername()} successfully logged in as {username}.")
                msg = username + b" logged in"
                self.sendall(len(msg).to_bytes(1,"big") + msg)

        def stop(self):
            self.running = False
            self.write_log("Server shut down")
            self.co.close()
            self.logfile.close()


if __name__ == '__main__':
    Server().start()
