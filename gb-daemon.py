#!/usr/bin/env python3




""" 
 The gaerbox controls the temperature in the gaerbox while listening on a local socket for commands.
"""

import os
import sys
import time
import json
import re

import configparser
import logging

import socket
from threading import Thread

import systemd.daemon

from gaerbox import DB, TemperatureSensor, Heating


########################################################
# read config
#
conf_file = '/etc/gaerbox.conf'
if not os.path.exists(conf_file):
    conf_file = 'etc/gaerbox.conf'
if not os.path.exists(conf_file):
    logging.error('No config file found.')
    sys.exit(1)

config = configparser.ConfigParser()
conf = config.read(conf_file)


try: 
    maxtemp = int(config['daemon']['maxtemp'])
except KeyError:
    logging.debug('maxtemp setting not found in config. Using default value')
    maxtemp = 32

try: 
    mintemp = int(config['daemon']['mintemp'])
except KeyError:
    logging.debug('mintemp setting not found in config. Using default value')
    mintemp = 28

try: 
    dt = int(config['daemon']['dt'])
except KeyError:
    logging.debug('dt setting not found in config. Using default value')
    dt = 20
    
# FIXME: check user input for validity

try:
    sensor = config['daemon']['sensor']
except KeyError:
    logging.fatal('ERROR: sensor path not defined')
    sys.exit(1)

if not os.path.exists(sensor):
    logging.fatal(f'ERROR: sensor path [{sensor}] does not exists.')
    sys.exit(1)

# socket settings
try:
    host = config['daemon']['host']
    port = int(config['daemon']['port'])
except KeyError:
    host = 'localhost'
    port = 45454



########################################################
 




class GaerboxDaemon(Thread):
    ''' gaearbox daemon, which checks the temperature and starts the heating device if necessary.'''

    def __init__(self):
        logging.info('starte daemon')
        super().__init__()
        self.running = True
        self.ta = -99
        self.mintemp = 20
        self.maxtemp = 22  # just a default value to start from
        self.set_maxtemp(maxtemp)
        self.set_mintemp(mintemp)
        self.heat = Heating()
        self.db = DB()

    def run(self):
        temp = TemperatureSensor(sensor)
        systemd.daemon.notify('READY=1')
        # self.running = True

        # while self.running:
        while True:
            try:
                temp.read_ta()
                self.ta = temp.ta
            except ValueError:
                logging.error('can not read temperature sensor')
                self.heat.off()
                # FIXME: mark sure, that the heating is switched off, when the temperature measurements fails.
                # FIXME: the evaluation below should not be performed in case of error.
            if self.running:
                if temp.ta <= self.mintemp and self.heat.status == 0:
                    self.heat.on()
                if temp.ta >= self.maxtemp and self.heat.status == 1:
                    self.heat.off()
            else:
                if self.heat.status == 1:
                    self.heat.off()
                logging.debug('daemon is passive')
            msg = json.dumps({'ta': round(temp.ta, 1), 'heating': self.heat.status, 
                              'mintemp': self.mintemp, 'maxtemp': self.maxtemp})
            logging.debug(f"> {msg}")
            # save to database
            self.db.add_temp(temp.ta, self.heat.status, self.mintemp, self.maxtemp)
            time.sleep(dt)
            # i=0
            # while i <= dt:
                # if not self.running:
                    # return
                # time.sleep(1)
                # i=i+1

    def quit(self):
        self.running = False
        self.heat.off()
        self.heat.shutdown()
        self.db.close()

    def set_mintemp(self, newmintemp):
        logging.info(f'mintemp changed from {self.mintemp} to {newmintemp}')
        # a few validity check
        if newmintemp < self.maxtemp:
            self.mintemp = newmintemp

    def set_maxtemp(self, newmaxtemp):
        logging.info(f'maxtemp changed from {self.maxtemp} to {newmaxtemp}')
        self.maxtemp = newmaxtemp
        # a few validity check
        if newmaxtemp < self.mintemp:
            self.maxtemp = newmaxtemp


    def pause(self):
        self.running = False


    def restart(self):
        self.running = True


def main(arguments):

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")

    # start the gaerbox Daemon
    gbdaemon = GaerboxDaemon()
    gbdaemon.start()


    logging.info(f"Listening for commands on {host}:{port}")

    # socket.setdefaulttimeout(10)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    # FIXME: so far, a single connection blocks all other clients
    #        a. a time out should ensure, that inactive clients get disconnected
    #        b. allow multiple connections

    # https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method

    try:
        # client_timeout = 10
        while True:
            s.listen()
            conn, addr = s.accept()
            # maybe we should allow multiple connections oin the future.
            # then the part below should run in an own thread.
            #          (clientsocket, address) = serversocket.accept()
            #          #  now do something with the clientsocket
            #          # in this case, we'll pretend this is a threaded server
            #          ct = client_thread(clientsocket)
            #          ct.run()
            with conn:
                # client_start = time.time()
                print(addr)
                logging.info('Connected by %s %s' % addr)
                mintemp_pattern = re.compile("mintemp_([0-3][0-9](\.[0-9])?)")
                maxtemp_pattern = re.compile("maxtemp_([0-3][0-9](\.[0-9])?)")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    data = data.decode('utf8')
                    data = data.rstrip('\r\n')
                    data = data.rstrip('\n')
                    data = data.lower()
                    logging.debug(f"got: {data}")
                    # possible commands:
                    #   pause : stop daemon
                    #   start : start daemon
                    # force heat on|off
                    # poweroff : shutdown system
                    # temprange 22, 28  : set new mintemp and maxtemp. triggers a restart of the daemon with the new settings
                    if data == 'pause':
                        gbdaemon.pause()
                        conn.sendall(b'ok. daemon stopped\n')
                        continue
                    if data == 'start':  # FIXME call it continue???
                        gbdaemon.restart()
                        conn.sendall(b'ok. daemon restarted.\n')
                        continue
                    if data == 'heat_on':
                        gbdaemon.heat.on()
                        conn.sendall(b'ok. heating started .\n')
                        continue
                    if data == 'heat_off':
                        gbdaemon.heat.off()
                        conn.sendall(b'ok. heating stopped.\n')
                        continue
                    if mintemp_pattern.match(data):
                        found = mintemp_pattern.search(data)
                        try:
                            value = found.group(1)
                            print(value)
                            value = float(value)
                            gbdaemon.set_mintemp(value)
                            conn.sendall(b'ok')
                        except e:
                            print(e)
                        continue
                    if maxtemp_pattern.match(data):
                        found = maxtemp_pattern.search(data)
                        try:
                            value = found.group(1)
                            print(value)
                            value = float(value)
                            gbdaemon.set_maxtemp(value)
                            conn.sendall(b'ok')
                        except e:
                            print(e)
                        continue
                    if data == 'quit':
                        conn.sendall(b'ciao!\n')
                        conn.close()
                        break
                    if data == 'poweroff':
                        # TODO: 
                        conn.sendall(b'ok, poweroff. NOT IMPLEMENTED YET.\n')
                        conn.close()
                        cmd = 'sudo shutdown -h now'
                        #system(cmd)
                        break
                    if data == 'status':
                        msg = b'\n'
                        if gbdaemon.running:
                            msg += b"Gaerbox is running\n"
                        else:
                            msg += b"Gaerbox is stopped\n"
                        msg += b"The current temperature is %2.1f\xc2\xb0C.\n" % gbdaemon.ta
                        if gbdaemon.heat.status == 1:
                            msg += b"Heating is switch on.\n"
                        else:
                            msg += b"Heating is switch off.\n"
                        msg += b"The current temperature range is %2.1f - %2.1f\xc2\xb0C.\n" % (
                                                             gbdaemon.mintemp, gbdaemon.maxtemp)
                        conn.sendall(msg)
                        conn.close()
                        break
                    # if time.time() - client_start > client_timeout:
                        # conn.sendall(b'connection timed uut.\n')
                        # conn.close()
                    ## ELSE
                    conn.sendall(b'do not understand what you mean!\n')
                    conn.close()
                    break
    except KeyboardInterrupt:
        logging.info('got keyboard interrupt. will clean up and stop now.')
        pass

    s.close()
    gbdaemon.quit()

    sys.exit(0)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
