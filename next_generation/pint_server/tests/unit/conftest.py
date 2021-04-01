import mock
import os
import pytest

os.environ = mock.MagicMock()

from pint_server import app

@pytest.fixture(scope='session')
def client():
    flask_app = app.app
    flask_app.config['TESTING'] = True

    with flask_app.test_client() as client:
        yield client
