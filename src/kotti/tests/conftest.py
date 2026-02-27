from pytest import fixture
from pytest import skip


# ``py.test --runslow`` causes the entire testsuite to be run, including test
# that are decorated with ``@@slow`` (scaffolding tests).
# see http://pytest.org/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option  # noqa


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not item.config.getoption("--runslow"):
        skip("need --runslow option to run")


# non-public test fixtures


@fixture
def app(db_session, setup_app):
    from webtest import TestApp

    return TestApp(setup_app)


@fixture
def extra_principals(db_session):
    """ Setup additional users 'bob', 'frank' and groups 'bobsgroup' and
    'franksgroup'.  Return the result of ``get_pricipals()``. """

    from kotti.security import get_principals

    P = get_principals()
    P["bob"] = dict(name="bob", title="Bob")
    P["frank"] = dict(name="frank", title="Frank")
    P["group:bobsgroup"] = dict(name="group:bobsgroup", title="Bob's Group")
    P["group:franksgroup"] = dict(name="group:franksgroup", title="Frank's Group")
    return P
