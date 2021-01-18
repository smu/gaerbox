

INSTALLDIR = /usr/local/



install: 
	# this is a bit too quick and dirty
	# binaries and libs
	cp -r gaerbox $(INSTALLDIR)/lib/python3.7/dist-packages/
	cp gb-daemon.py $(INSTALLDIR)/bin/
	cp gb-client.py $(INSTALLDIR)/bin/
	ln -s $(INSTALLDIR)/bin/gb-client.py $(INSTALLDIR)/bin/gbc
	# settings
	cp etc/gb.conf /etc/
	[ -d /var/lib/gaerbox/ ] || mkdir /var/lib/gaerbox/
	# systemd
	cp etc/systemd/system/gaerbox.service /lib/systemd/system
	chmod 644 /lib/systemd/system/gaerbox.service
	systemctl enable gaerbox.service
	systemctl start gaerbox.service



uninstall: 
	rm -f $(INSTALLDIR)/bin/gb-daemon.py
	rm -f /etc/gb.conf
	rm -rf $(INSTALLDIR)/lib/python3.7/dist-packages/gaerbox/

	systemctl stop gaerbox.service
	systemctl disable gaerbox.service
	rm -f /lib/systemd/system/gaerbox.service
	# rm -f /var/lib/gaerbox/temperatures.sqlite
	rm -f $(INSTALLDIR)/bin/gb-client.py
	rm -f $(INSTALLDIR)/bin/gbc


reinstall: uninstall install
