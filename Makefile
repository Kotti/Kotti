
version = 2.7
python = python$(version)

test: bin/py.test
	bin/py.test -q -n4

bin/py.test: .pip.log *.py *.cfg
	bin/pip install -e ".[testing]"
	@touch $@

.pip.log: bin/python
	bin/pip install -e ".[development]" --log .pip.log

bin/python:
	virtualenv-$(version) .
	@touch $@

clean:
	@rm -rfv bin/ include/ lib/ share/ .Python .cache .eggs Kotti.db Kotti.egg-info tox

.PHONY: test clean
