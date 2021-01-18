# gaerbox

Maintain the temperature in a proofing box ("Gärbox" in german) using a
raspberry pi and bit of hardware.

## gaerbox daemon

A daemon script `gb-daemon.py` monitors the temperature and activates or
deactivates the heat source, to keep the temperature in the box within the
configured temperature range. The heating is active, as long as the temperature
in the box is below `maxtemp`. When the temperature in the box reaches
`maxtemp`, the heating is switched off, until `mintemp` is reached again. The
default settings are configures in `/etc/gaerbox.conf`.
The daemon is started by systemd during boot.



## gaerbox client

The client script `gb-client.py` is used to query the current temperature of the
box and to modify the minimum and maximum temperature in the box and other
settings. The client must run locally on the same system as the daemon. Therefore, `ssh`
access to the raspberry pi is needed.

The following commands are supported by `gb-client.py`

```
$ gb-client.py --help
usage: gbc [-h] [-mintemp MINTEMP] [-maxtemp MAXTEMP] [-status] [-stop]
           [-start] [-heat {on,off}] [-poweroff]

gaerbox client: allows to send commands to the gaerbox daemon, e.g. change the
minimum temperature or stop the daemon

optional arguments:
  -h, --help        show this help message and exit
  -mintemp MINTEMP  Set minimum temperature
  -maxtemp MAXTEMP  Set maximum temperature
  -status           Query some status information from the daemon
  -stop             Stop the daemon
  -start            Start the daemon
  -heat {on,off}    Switch heating on or off
  -poweroff         Shutdown the system
```


## Hardware requirements

 * raspberry pi
 * a well isolated box
 * a heat source, e.g. a heating mat for terrarium
 * a temperature sensor (I used the DS18B20)
 * a relay
 

## installation

so far a quick&dirty `Makefile` exist, which allows to install and deinstall `gaerbox`
on `Raspbian GNU/Linux 10 (buster)`.

# my setup
 
todo...


## Next steps...

 * control the daemon using some kind of web application...
