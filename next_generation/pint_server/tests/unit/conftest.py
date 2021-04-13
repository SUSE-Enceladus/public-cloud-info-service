import mock
import os
import pytest
import sqlalchemy

os.environ = mock.MagicMock()
sqlalchemy.create_engine = mock.MagicMock()

from pint_server import app

@pytest.fixture(scope='session')
def client():
    flask_app = app.app
    flask_app.config['TESTING'] = True

    with flask_app.test_client() as client:
        yield client
