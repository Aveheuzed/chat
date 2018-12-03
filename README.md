# chat client/server


# usage

  * client

    `client.py`

  * server

    `server.py` will launch a server on port *1337* (can be changed using the `PORT` constant)

# dependencies / setup

  The client needs **tkinter** to work.

  You need **python3** to run both client or server parts (tests and dev under python3.6).

  There's no setup required, just launch the script ! (You'll need your URL/*public* IP if you're running the server side)

# protocol

  Current protocol (all under TCP on port 1337) :
  1. The client sends the server its version number
  2. Server answer : `\x01` if the server supports that version, `\x00` + exits otherwise
  4. The client sends the user's login, prefixed by its length (one-byte, unsigned)
  5. If that login is registered *and not currently in use*, the server accepts it and send `\x01` ; else, `\x00` + back to previous step.
  5. The server generates a random 32-bytes salt and sends it to the client
  5. The client hashes the user's password + salt (with cipher.HASHFUNC), and sends it back to the server
  5. If this hash doesn't match the server's, back to the ask login step
  6. Proper chat : the client sends ciphered messages, the server deciphers it and broadcasts it (ciphered) to each currently connected clients.

# main chat messages

  * plain structure :
    * first byte : length of the message for text message, 0 for special actions
    * following bytes : message itself (if no special action)
  * special actions :

    i.e. changing their *own* password, creating a new user, or shutting the server down. The only unprivileged action authorized is the first one. Changing their own password doesn't change nothing to ciphering matters : the old password is kept until end-of-session.
    Structure of the special actions may be found in comments in the `server.ClientHandler.read_message` method.

  * **ciphering** :

    The whole of the messages are ciphered, using  `cipher.Cipherer`.
    To ensure correct deciphering, the client [de]ciphering machines and the user's must be kept on the same state (use them only to send/receive messages).

    The hash of the user's password is the ciphering key, that is to say the hash seed. (read `cipher.py` for details)

# Registering to a Server

  The server uses a pickle password database, containing a `{username : hashed_password}` dict.

  This gives the server access to hashed passwords, allowing it to hash them again with a random salt.

  At startup, if no password database is found, using the `DB_PATH` server constant, a new one is created at that path, and the admin is prompted for a passsword (the associated login is *admin*). The *admin* account has additionnal features (read *special actions*)

  From that point on, it is only possible to register to the server from an existing account, using a special action (read *main chat messages*)
