
test: bin/pytest
	bin/pytest -q -n4

bin/pytest: .pip.log *.py *.cfg
	bin/pip install -e ".[testing]"
	@touch $@

.pip.log: bin/python
	bin/pip install -e ".[development]" --log .pip.log

bin/python:
	virtualenv --clear .
	@touch $@

clean:
	@rm -rfv bin/ include/ lib/ share/ .Python .cache .eggs Kotti.db Kotti.egg-info .tox

.PHONY: test clean
