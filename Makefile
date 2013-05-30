
all: install

clean:
	rm -fr *.egg-info dist build

scrub: clean
	rm -fr $(ve)

ve=$(PWD)/ve
python=$(ve)/bin/python
ve: $(ve)
$(ve):
	virtualenv --system-site-packages $@

install: $(ve)
	$(python) setup.py install
develop:
	$(python) setup.py develop

monitor:
	$(ve)/bin/tailall /var/log
