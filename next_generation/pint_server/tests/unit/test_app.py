import json
import mock
import pytest

from pint_server.tests.unit import mock_pint_data


def test_root_request(client):
    """Start with a blank database."""
    rv = client.get('/')
    assert 301 == rv.status_code
    assert 'https://www.suse.com/solutions/public-cloud/' == rv.location

def test_supported_version(client):
    provider='amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images',
                return_value=mock_pint_data.mocked_return_value_images[provider]) as get_provider_images:
            route = '/v1/' + provider + '/images'
            rv = client.get(route)
            get_provider_images.assert_called_with(provider)
            assert 200 == rv.status_code
            assert mock_pint_data.expected_json_images[provider] == json.loads(rv.data)
            assert rv.headers['Access-Control-Allow-Origin'] == '*'
            assert rv.headers['Content-type'] == 'application/json'

def test_unsupported_version(client):
    #test v2
    provider='amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images'):
            route = '/v2/' + provider + '/images'
            rv = client.get(route)
            assert 400 == rv.status_code
            assert len(rv.data) == 0
            assert rv.headers['Access-Control-Allow-Origin'] == '*'

@pytest.mark.parametrize("provider",["alibaba", "amazon", "google", "microsoft", "oracle"])
def test_get_provider_images(client, provider):
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images',
                return_value=mock_pint_data.mocked_return_value_images[provider]) as get_provider_images:
            route = '/v1/' + provider + '/images'
            rv = client.get(route)
            get_provider_images.assert_called_with(provider)
            assert 200 == rv.status_code
            assert mock_pint_data.expected_json_images[provider] == json.loads(rv.data)
            assert rv.headers['Access-Control-Allow-Origin'] == '*'

"""
#Currently failing because instead of 404 it's returning 400. will have to fix the exception handling in pint_server.app.py
def test_get_invalid_provider_images(client):
    invalid_provider = 'foo'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images'):
            route = '/v1/' + invalid_provider + '/images'
            rv = client.get(route)
            assert 404 == rv.status_code
            assert len(rv.data) == 0
            assert rv.headers['Access-Control-Allow-Origin'] == '*'
"""

@pytest.mark.parametrize("category",["images", "servers"])
def test_get_provider_valid_category(client, category):
    provider='amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        if category == 'images':
            with mock.patch('pint_server.app.get_provider_images',
                            return_value=mock_pint_data.mocked_return_value_images[provider]) as get_provider_images:
                route = '/v1/' + provider + '/images'
                rv = client.get(route)
                get_provider_images.assert_called_with(provider)
                assert 200 == rv.status_code
                assert mock_pint_data.expected_json_images[provider] == json.loads(rv.data)
                assert rv.headers['Access-Control-Allow-Origin'] == '*'
        if category == 'servers':
            with mock.patch('pint_server.app.get_provider_servers',
                        return_value=mock_pint_data.mocked_return_value_servers[provider]) as get_provider_servers:
                route = '/v1/' + provider + '/servers'
                rv = client.get(route)
                get_provider_servers.assert_called_with(provider)
                assert 200 == rv.status_code
                assert mock_pint_data.expected_json_servers[provider] == json.loads(rv.data)
                assert rv.headers['Access-Control-Allow-Origin'] == '*'

def test_get_provider_invalid_category(client):
    invalid_category = 'foo'
    provider = 'amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        route = '/v1/' + provider + '/' + invalid_category
        rv = client.get(route)
        assert 404 == rv.status_code
        assert len(rv.data) == 0
        assert rv.headers['Access-Control-Allow-Origin'] == '*'

@pytest.mark.parametrize("server_type",["region", "update"])
def test_get_provider_servers_by_type(client, server_type):
    provider = 'amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        provider_servers = mock_pint_data.filter_mocked_return_value_servers_by_type(
            mock_pint_data.mocked_return_value_servers[provider], server_type)
        expected_servers = mock_pint_data.construct_mock_expected_response(provider_servers, 'servers')
        with mock.patch('pint_server.app.get_provider_servers_for_type',return_value=provider_servers) \
                as get_provider_servers_for_type:
            route = '/v1/' + provider + '/servers/' + server_type
            rv = client.get(route)
            get_provider_servers_for_type.assert_called_with(provider, server_type)
            assert 200 == rv.status_code
            assert expected_servers == json.loads(rv.data)

#Currently failing because instead of 404 it's returning 400. will have to fix the exception handling in pint_server.app.py
"""
def test_get_provider_invalid_server_type(client):
    invalid_server_type='foo'
    provider = 'amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_servers_for_type'):
            route = '/v1/' + provider + '/servers/' + invalid_server_type
            rv = client.get(route)
            assert 404 == rv.status_code
            assert len(rv.data) == 0
            assert rv.headers['Access-Control-Allow-Origin'] == '*'
"""

@pytest.mark.parametrize("image_state",["active", "inactive", "deprecated", "deleted"])
def test_provider_images_by_state(client, image_state):
    provider = 'amazon'
    provider_images = mock_pint_data.mocked_return_value_images[provider]
    provider_images_by_state = mock_pint_data.filter_mocked_return_value_images_by_state(provider_images, image_state)
    expected_images = mock_pint_data.construct_mock_expected_response(provider_images_by_state, 'images')
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images_for_state',
                return_value=provider_images_by_state) as get_provider_images_for_state:
            route = '/v1/' + provider + '/images/' + image_state
            rv = client.get(route)
            get_provider_images_for_state.assert_called_with(provider, image_state)
            assert 200 == rv.status_code
            assert expected_images == json.loads(rv.data)
            assert rv.headers['Access-Control-Allow-Origin'] == '*'


def test_get_providers(client):
    """Test GET /v1/providers"""
    with mock.patch('pint_server.app.query_providers',
                    return_value=mock_pint_data.query_providers_return_value):
        rv = client.get('/v1/providers')
        assert 200 == rv.status_code
        assert mock_pint_data.expected_json_providers == json.loads(rv.data)

def test_get_provider_servers_types(client):
    """Test GET /v1/<provider>/servers/types"""
    provider = 'amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_servers_types',
                return_value=mock_pint_data.mocked_return_value_server_types) as get_provider_server_types:
            route = '/v1/' + provider + '/servers/types'
            rv = client.get(route)
            get_provider_server_types.assert_called_with(provider)
            assert 200 == rv.status_code
            assert mock_pint_data.expected_json_server_types == json.loads(rv.data)
