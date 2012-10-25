
version = 2.7
python = python$(version)

test: bin/py.test
	bin/py.test -q -n4

bin/py.test: .pip.log *.py *.cfg
	bin/python setup.py dev
	@touch $@

.pip.log: bin/python requirements.txt
	bin/pip install -r requirements.txt --log .pip.log

bin/python:
	virtualenv-$(version) --no-site-packages --distribute .
	@touch $@

clean:
	@rm -rfv bin/ include/ lib/

.PHONY: test clean

