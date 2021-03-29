import json
import mock
import os
import tempfile

os.environ = mock.MagicMock()

import app
import pytest

@pytest.fixture
def client():
    flask_app = app.app
    flask_app.config['TESTING'] = True

    with flask_app.test_client() as client:
        yield client

#    os.close(db_fd)
#    os.unlink(app.app.config['DATABASE'])


def test_root_request(client):
    """Start with a blank database."""

    rv = client.get('/')
    assert 301 == rv.status_code
    assert 'https://www.suse.com/solutions/public-cloud/' == rv.location


def test_get_providers(client):
    """Test GET /v1/providers"""

    query_providers_return_value = ['amazon', 'microsoft', 'google', 'alibaba',
                                    'oracle']
    expected_json = {'providers':
                        [
                            {'name': 'amazon'},
                            {'name': 'microsoft'},
                            {'name': 'google'},
                            {'name': 'alibaba'},
                            {'name': 'oracle'}
                        ]
                    }
    with mock.patch('app.query_providers',
                    return_value=query_providers_return_value):
        rv = client.get('/v1/providers')
        assert 200 == rv.status_code
        assert expected_json == json.loads(rv.data)


def test_get_provider_servers_types(client):
    """Test GET /v1/<provider>/servers/types"""

    mocked_return_value = ['region', 'update']
    expected_json = {'types': ['region', 'update']}
    with mock.patch('app.assert_valid_provider'):
        with mock.patch('app.get_provider_servers_types',
                return_value=mocked_return_value) as get_provider_server_types:
            rv = client.get('/v1/amazon/servers/types')
            get_provider_server_types.assert_called_with('amazon')
            assert 200 == rv.status_code
            assert expected_json == json.loads(rv.data)

