# chat client/server


1. use
------

  * client

    `__main__.py`

  * server

  `__main__.py -s` will launch a server on port *1337* (can be changed using the `PORT` contant)

2. dependencies - setup
-----------------------

  This needs **tkinter** to work correctly, even on server side (witch doesn't, of course, display anything)

  You need **python3** to run it (tests and dev under python3.6).

  There's no setup required, just launch it ! (You'll need your URL/*public* IP if you're running the server side)

3. protocol
-----------

  Current protocol (all under TCP on port 1337) :
  1. The client sends the server its version number
  2. Server answer : `\x01` if the server supports that version, `\x00` + exits otherwise
  3. For each subsequent communication, the client prefixes what it sends with its length (one-byte, unsigned)
  4. The client sends user's login
  5. If that login is free, the server accepts it and send `\x01` ; else, `\x00` + back to previous step.
  6. Proper chat : the client sends messages, the server boradcasts it to each currently connected clients.

4. exit codes (client side)
------------

  * 0 : no error
  * 1 : user cancelled
  * 2 : obsolete client
  * 3 : bad command-line argument(s)
