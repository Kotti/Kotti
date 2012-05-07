# b/w compat

from kotti.testing import _initTestingDB
from kotti.testing import _turn_warnings_into_errors
from kotti.testing import BASE_URL
from kotti.testing import Dummy
from kotti.testing import dummy_view
from kotti.testing import DummyRequest
from kotti.testing import EventTestBase
from kotti.testing import FunctionalTestBase
from kotti.testing import include_testing_view
from kotti.testing import registerDummyMailer
from kotti.testing import setUp
from kotti.testing import setUpFunctional
from kotti.testing import setUpFunctionalStrippedDownApp
from kotti.testing import tearDown
from kotti.testing import testing_db_url
from kotti.testing import TestingRootFactory
from kotti.testing import UnitTestBase


__all__ = [
    '_initTestingDB',
    '_turn_warnings_into_errors',
    'BASE_URL',
    'Dummy',
    'dummy_view',
    'DummyRequest',
    'EventTestBase',
    'FunctionalTestBase',
    'include_testing_view',
    'registerDummyMailer',
    'setUp',
    'setUpFunctional',
    'setUpFunctionalStrippedDownApp',
    'tearDown',
    'testing_db_url',
    'TestingRootFactory',
    'UnitTestBase',
]
