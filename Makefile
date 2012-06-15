
version = 2.7
python = python$(version)

test: bin/py.test
	bin/py.test -q -n4

bin/py.test: bin/python *.py *.cfg
	bin/python setup.py dev
	@touch $@

bin/python:
	virtualenv-$(version) --no-site-packages --distribute .
	@touch $@

clean:
	@rm -rfv bin/ include/ lib/

.PHONY: test clean

