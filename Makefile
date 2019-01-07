
test: bin/pytest
	bin/pytest

bin/pytest: .pip.log *.py *.cfg
	bin/pip install -e ".[testing]"
	@touch $@

.pip.log: bin/python
	bin/pip install -e ".[development]" --log .pip.log

bin/python:
	python -m venv .
	@touch $@

clean:
	@rm -rfv bin/ include/ lib/ share/ .Python .cache .eggs Kotti.db Kotti.egg-info .tox

.PHONY: test clean
