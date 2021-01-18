import os
import logging
from datetime import datetime
import sqlite3
import RPi.GPIO as GPIO

class TemperatureSensor():
    ''' Read the current temperature from the temperature sensor.'''

    # helpful references:
    #   * https://st-page.de/2018/01/20/tutorial-raspberry-pi-temperaturmessung-mit-ds18b20/

    def __init__(self, sensor):
        self.sensor = sensor
        self.NAval = -99
        self.ta = self.NAval

    def read_sensor(self):
        with open(self.sensor, 'r') as f:
            lines = f.readlines()
            return(lines)

    def read_ta(self):
        """Aus dem Systembus lese ich die Temperatur der DS18B20 aus.
          based on: https://st-page.de/2018/01/20/tutorial-raspberry-pi-temperaturmessung-mit-ds18b20/"""
        lines = self.read_sensor()
        i = 0
        while lines[0].strip()[-3:] != 'YES' and i < 10:
            time.sleep(0.2)
            lines = self.read_sensor()
            i = i+1
        temperaturStr = lines[1].find('t=')
        if temperaturStr != -1 :
            tempData = lines[1][temperaturStr+2:]
            tempCelsius = float(tempData) / 1000.0
            self.ta = tempCelsius
        else:
            self.ta = self.NAval
            raise ValueError
        return 


class Heating():
    ''' controll the heating device '''

    def __init__(self):
        self.status = 0
        GPIO.setmode(GPIO.BCM)      # GPIO Nummern statt Board Nummern
        self.RELAIS_GPIO = 18       # FIXME: add to config
        GPIO.setup(self.RELAIS_GPIO, GPIO.OUT) # GPIO Modus zuweisen
        self.off()

    def on(self):
        logging.info('Heating switched on')
        GPIO.output(self.RELAIS_GPIO, GPIO.LOW) 
        self.status = 1

    def off(self):
        logging.info('Heating switched off')
        self.status = 0
        GPIO.output(self.RELAIS_GPIO, GPIO.HIGH)


    def shutdown(self):
        GPIO.cleanup()


class DB():
    ''' database interface '''

    def __init__(self, dbfile='/var/lib/gaerbox/database.sqlite', ro=False):
        self.ro = ro
        if not ro:
            if not os.path.exists(dbfile):
                print('erstelle db schema')
                conn = sqlite3.connect(dbfile, check_same_thread=False)
                c = conn.cursor()
                # Create table
                c.execute('''CREATE TABLE measurements
                                 (date text, ta real, heating int, tamin real, tamax real)''')
                conn.commit()
                # c.execute('''CREATE TABLE runs
                                 # (date text, run int)''')
                # conn.commit()
            else:
                conn = sqlite3.connect(dbfile, check_same_thread=False)
        else:
            if not os.path.exists(dbfile):
                logging.error('Database not found')
                return
            dbfile_uri = "file:%s?mode=ro" % dbfile
            conn  = sqlite3.connect(dbfile_uri, uri=True)
        self.conn = conn

    def close(self):
        self.conn.close()

    def add_temp(self, ta, heating, tamin, tamax):
        if not self.ro:
            now = datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
            c = self.conn.cursor()
            c.execute('INSERT INTO measurements VALUES (?,?,?, ?, ?)', [now, ta, heating, tamin, tamax])
            self.conn.commit()
        else:
            logging.error('database in read-only mode')

    def get_latest_temp(self):
        c = self.conn.cursor()
        c.execute('SELECT date, ta, heating, tamin, tamax FROM measurements ORDER BY date DESC limit 1')
        rows = c.fetchall()
        return(rows[0])
