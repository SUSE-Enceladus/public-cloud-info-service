import json
import mock
import pytest

from pint_server.tests.unit import mock_pint_data

def test_root_request(client):
    """Start with a blank database."""
    rv = client.get('/')
    assert 301 == rv.status_code
    assert 'https://www.suse.com/solutions/public-cloud/' == rv.location

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_supported_version(client, extension):
    provider = 'amazon'
    value = mock_pint_data.mocked_return_value_images[provider]
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images',
                        return_value=value) as get_provider_images:
            route = '/v1/' + provider + '/images' + extension
            rv = client.get(route)
            get_provider_images.assert_called_with(provider)
            validate(rv, 200, extension)
            if extension != '.xml':
                assert mock_pint_data.expected_json_images[provider] == json.loads(rv.data)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_unsupported_version(client, extension):
    # test v2
    provider = 'amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images'):
            route = '/v2/' + provider + '/images' + extension
            rv = client.get(route)
            validate(rv, 400, extension)


@pytest.mark.parametrize("provider", ["alibaba", "amazon", "google", "microsoft", "oracle"])
@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_provider_images(client, provider, extension):
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images',
                        return_value=mock_pint_data.mocked_return_value_images[provider]) as get_provider_images:
            route = '/v1/' + provider + '/images' + extension
            rv = client.get(route)
            get_provider_images.assert_called_with(provider)
            validate(rv, 200, extension)
            if extension != '.xml':
                assert mock_pint_data.expected_json_images[provider] == json.loads(rv.data)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("category", ["images", "servers"])
@pytest.mark.parametrize("provider", ['amazon', 'microsoft', 'google', 'alibaba', 'oracle'])
def test_get_provider_valid_category(client, provider, category, extension):
    with mock.patch('pint_server.app.assert_valid_provider'):
        if category == 'images':
            with mock.patch('pint_server.app.get_provider_images',
                            return_value=mock_pint_data.mocked_return_value_images[provider]) as get_provider_images:
                route = '/v1/' + provider + '/images' + extension
                rv = client.get(route)
                get_provider_images.assert_called_with(provider)
                validate(rv, 200, extension)
                if extension != '.xml':
                    assert mock_pint_data.expected_json_images[provider] == json.loads(rv.data)

        if category == 'servers':
            with mock.patch('pint_server.app.get_provider_servers',
                            return_value=mock_pint_data.mocked_return_value_servers[provider]) as get_provider_servers:
                route = '/v1/' + provider + '/servers' + extension
                rv = client.get(route)
                get_provider_servers.assert_called_with(provider)
                validate(rv, 200, extension)
                if extension != '.xml':
                    assert mock_pint_data.expected_json_servers[provider] == json.loads(rv.data)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_provider_invalid_category(client, extension):
    invalid_category = 'foo'
    provider = 'amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        route = '/v1/' + provider + '/' + invalid_category + extension
        rv = client.get(route)
        validate(rv, 400, extension)

@pytest.mark.parametrize("server_type", ["region", "update"])  # regionserver, smt from original pint
@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['amazon', 'microsoft', 'google', 'alibaba', 'oracle'])
def test_get_provider_servers_by_type(client, provider, server_type, extension):
    with mock.patch('pint_server.app.assert_valid_provider'):
        provider_servers = mock_pint_data.filter_mocked_return_value_servers_by_type(
            mock_pint_data.mocked_return_value_servers[provider], server_type)
        expected_servers = mock_pint_data.construct_mock_expected_response(provider_servers, 'servers')
        with mock.patch('pint_server.app.get_provider_servers_for_type', return_value=provider_servers) \
                as get_provider_servers_for_type:
            route = '/v1/' + provider + '/servers/' + server_type + extension
            rv = client.get(route)
            get_provider_servers_for_type.assert_called_with(provider, server_type)
            validate(rv, 200, extension)
            if extension != '.xml':
                assert expected_servers == json.loads(rv.data)

@pytest.mark.parametrize("image_state", ["active", "inactive", "deprecated", "deleted"])
@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['amazon', 'microsoft', 'google', 'alibaba', 'oracle'])
def test_get_provider_images_by_state(client, provider, image_state, extension):
    provider_images = mock_pint_data.mocked_return_value_images[provider]
    provider_images_by_state = mock_pint_data.filter_mocked_return_value_images_by_state(provider_images, image_state)
    expected_images = mock_pint_data.construct_mock_expected_response(provider_images_by_state, 'images')
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images_for_state',
                        return_value=provider_images_by_state) as get_provider_images_for_state:
            route = '/v1/' + provider + '/images/' + image_state + extension
            rv = client.get(route)
            get_provider_images_for_state.assert_called_with(provider, image_state)
            validate(rv, 200, extension)
            if extension != '.xml':
                assert expected_images == json.loads(rv.data)

@pytest.mark.parametrize("category", ["images", "servers"])
@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_regions_category(client, provider, category, extension):
    mock_valid_regions = []
    for each in mock_pint_data.mocked_return_value_regions[provider]:
        mock_valid_regions.append(each['name'])
    for region in mock_valid_regions:
        with mock.patch('pint_server.app.assert_valid_provider'):
            with mock.patch('pint_server.app.assert_valid_category'):
                if category == 'images':
                    provider_images = mock_pint_data.mocked_return_value_images[provider]
                    provider_images_by_region = mock_pint_data.filter_mocked_return_value_images_region(provider_images,
                                                                                                        region)
                    expected_images = mock_pint_data.construct_mock_expected_response(provider_images_by_region,
                                                                                      'images')
                    with mock.patch('pint_server.app.get_provider_images_for_region',
                                    return_value=provider_images_by_region) as get_provider_images_for_region:
                        route = '/v1/' + provider + '/' + region + '/images' + extension
                        rv = client.get(route)
                        get_provider_images_for_region.assert_called_with(provider, region)
                        validate(rv, 200, extension)
                        if extension != '.xml':
                            assert expected_images == json.loads(rv.data)

                if category == 'servers':
                    provider_servers = mock_pint_data.mocked_return_value_servers[provider]
                    provider_servers_by_region = mock_pint_data.filter_mocked_return_value_servers_region(
                        provider_servers, region)
                    expected_servers = mock_pint_data.construct_mock_expected_response(provider_servers_by_region,
                                                                                       'servers')
                    with mock.patch('pint_server.app.get_provider_servers_for_region',
                                    return_value=provider_servers_by_region) as get_provider_servers_for_region:
                        route = '/v1/' + provider + '/' + region + '/servers' + extension
                        rv = client.get(route)
                        get_provider_servers_for_region.assert_called_with(provider, region)
                        validate(rv, 200, extension)
                        if extension != '.xml':
                            assert expected_servers == json.loads(rv.data)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
@pytest.mark.parametrize("image_state", ['active', 'inactive', 'deleted', 'deprecated'])
def test_get_provider_regions_images_by_state(client, provider, image_state, extension):
    mock_valid_regions = []
    for each in mock_pint_data.mocked_return_value_regions[provider]:
        mock_valid_regions.append(each['name'])
    for region in mock_valid_regions:
        with mock.patch('pint_server.app.assert_valid_provider'):
            provider_images = mock_pint_data.mocked_return_value_images[provider]
            provider_images_by_region = mock_pint_data.filter_mocked_return_value_images_region(provider_images, region)
            provider_images_by_state = mock_pint_data.filter_mocked_return_value_images_by_state(
                provider_images_by_region, image_state)
            expected_images = mock_pint_data.construct_mock_expected_response(provider_images_by_state,
                                                                              'images')
            with mock.patch('pint_server.app.get_provider_images_for_region_and_state',
                            return_value=provider_images_by_state) as get_provider_images_for_region_and_state:
                route = '/v1/' + provider + '/' + region + '/images/' + image_state + extension
                rv = client.get(route)
                get_provider_images_for_region_and_state.assert_called_with(provider, region, image_state)
                validate(rv, 200, extension)
                if extension != '.xml':
                    assert expected_images == json.loads(rv.data)


@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
@pytest.mark.parametrize("type", ['region', 'update'])
def test_get_provider_regions_servers_by_type(client, provider, type, extension):
    mock_valid_regions = []
    for each in mock_pint_data.mocked_return_value_regions[provider]:
        mock_valid_regions.append(each['name'])
    for region in mock_valid_regions:
        with mock.patch('pint_server.app.assert_valid_provider'):
            provider_servers = mock_pint_data.mocked_return_value_servers[provider]
            provider_servers_by_region = mock_pint_data.filter_mocked_return_value_servers_region(provider_servers,
                                                                                                  region)
            provider_servers_by_type = mock_pint_data.filter_mocked_return_value_servers_by_type(
                provider_servers_by_region, type)
            expected_servers = mock_pint_data.construct_mock_expected_response(provider_servers_by_type,
                                                                               'servers')
            with mock.patch('pint_server.app.get_provider_servers_for_region_and_type',
                            return_value=provider_servers_by_type) as get_provider_servers_for_region_and_type:
                route = '/v1/' + provider + '/' + region + '/servers/' + type + extension
                rv = client.get(route)
                get_provider_servers_for_region_and_type.assert_called_with(provider, region, type)
                validate(rv, 200, extension)
                if extension != '.xml':
                    assert expected_servers == json.loads(rv.data)

@pytest.mark.parametrize("extension",['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_valid_region_invalidcategory(client, provider, extension):
    invalid_category='foo'
    mock_valid_regions = []
    for each in mock_pint_data.mocked_return_value_regions[provider]:
        mock_valid_regions.append(each['name'])
    for region in mock_valid_regions:
        with mock.patch('pint_server.app.assert_valid_provider'):
            route = '/v1/' + provider + '/' + region + invalid_category + extension
            rv = client.get(route)
            validate(rv, 400, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_provider_valid_category_extension(client, extension):
    provider = 'amazon'
    category = 'images'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_images',
                        return_value=mock_pint_data.mocked_return_value_images[provider]) as get_provider_images:
            route = '/v1/' + provider + '/' + category + extension
            rv = client.get(route)
            get_provider_images.assert_called_with(provider)
            validate(rv, 200, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_providers(client, extension):
    """Test GET /v1/providers"""
    with mock.patch('pint_server.app.get_supported_providers',
                    return_value=mock_pint_data.get_supported_providers_return_value):
        rv = client.get('/v1/providers' + extension)
        validate(rv, 200, extension)
        if extension != '.xml':
            assert mock_pint_data.expected_json_providers == json.loads(rv.data)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_provider_servers_types(client, extension):
    """Test GET /v1/<provider>/servers/types"""
    provider = 'amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_servers_types',
                        return_value=mock_pint_data.mocked_return_value_server_types) as get_provider_server_types:
            route = '/v1/' + provider + '/servers/types' + extension
            rv = client.get(route)
            get_provider_server_types.assert_called_with(provider)
            validate(rv, 200, extension)
            if extension != '.xml':
                assert mock_pint_data.expected_json_server_types == json.loads(rv.data)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_image_states(client, extension):
    with mock.patch('pint_server.app.list_images_states'):
        route = '/v1/images/states' + extension
        rv = client.get(route)
        validate(rv, 200, extension)
        if extension != '.xml':
            assert mock_pint_data.expected_json_image_states == json.loads(rv.data)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_provider_regions(client, extension):
    provider = 'amazon'
    with mock.patch('pint_server.app.assert_valid_provider'):
        with mock.patch('pint_server.app.get_provider_regions', return_value=mock_pint_data.mocked_return_value_regions[provider]):
            route = '/v1/' + provider + '/regions' + extension
            rv = client.get(route)
            validate(rv, 200, extension)
            if extension != '.xml':
                assert mock_pint_data.expected_json_regions[provider] == json.loads(rv.data)

def validate(rv, expected_status, extension):
    assert expected_status == rv.status_code
    assert rv.headers['Access-Control-Allow-Origin'] == '*'
    if expected_status == 200:
        if extension == '.xml':
            assert rv.headers['Content-Type'] == "application/xml;charset=utf-8"
            assert '<?xml version=' in rv.data.decode('utf-8')
        else:
            assert rv.headers['Content-Type'] == 'application/json'
            assert '{' in rv.data.decode('utf-8')
    else:
        # For 400, 404 content-type is set to text/html
        assert rv.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert len(rv.data) == 0
