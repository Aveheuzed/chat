#!/usr/bin/env python3
import sys

if len(sys.argv) < 2 :
        import guiclient
elif sys.argv[1] in ("--client","-c"):
        del sys.argv[1]
        import guiclient
elif sys.argv[1] in ("--server","-s") :
        del sys.argv[1]
        import main_server
elif sys.argv[1] in ("--killer","-k") :
        del sys.argv[1]
        import killer
else :
        print(""" Valid arguments :
        --client, -c [server's IP] : runs a graphic chat client ; if not given, the IP will be asked graphically ;
        --server, -s : runs a host on port 1337 (the others two are configured to work on that port, too) ;
        --killer, -k [server's IP] : shuts down remote server ; if not given, the IP will be asked in the console.
        Default behaviour (no argument) is the client.
        Any wrong first argument (--help, for instance ;) will display this help.
        Any wrong second argument will result in a crash.""")
