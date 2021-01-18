#!/usr/bin/env python3

""" 
gaerbox client: allows to send commands to the gaerbox daemon, e.g. change
the minimum temperature or stop the daemon 
"""

import sys, os
import socket
import logging
import configparser
import argparse

conf_file = '/etc/gaerbox.conf'
if not os.path.exists(conf_file):
    conf_file = 'etc/gaerbox.conf'
if not os.path.exists(conf_file):
    print('TODO: warning')

config = configparser.ConfigParser()
conf = config.read(conf_file)

# socket settings
try:
    host = config['daemon']['host']
    port = int(config['daemon']['port'])
except KeyError:
    host = 'localhost'
    port = 45454

def send_cmd(cmd):
    print('>> sending: %s' % cmd)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(cmd.encode('UTF-8'))
        data = s.recv(1024)
    data = str(data, 'utf-8')
    print("<< server said:  %s" % data)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-mintemp', help="Set minimum temperature", type=float)
    parser.add_argument('-maxtemp', help="Set maximum temperature", type=float)
    parser.add_argument('-status', help="Query some status information from the daemon", action='store_true', default=False)
    parser.add_argument('-stop', help="Stop the daemon", action='store_true', default=False)
    parser.add_argument('-start', help="Start the daemon", action='store_true', default=False)
    parser.add_argument('-heat', help="Switch heating on or off", choices=['on', 'off'])
    parser.add_argument('-poweroff', help="Shutdown the system", action='store_true', default=False)
    args = parser.parse_args(sys.argv[1:])
    # print(args)

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.maxtemp:
        send_cmd("maxtemp_%s" % args.maxtemp)

    if args.mintemp:
        send_cmd("mintemp_%s" % args.mintemp)

    if args.stop:
        send_cmd('pause')

    if args.start:
        send_cmd('start')

    if args.status:
        send_cmd('status')

    if args.poweroff:
        send_cmd('poweroff')

    if args.heat:
        send_cmd("heat_%s" % args.heat)

    
    sys.exit(0)
