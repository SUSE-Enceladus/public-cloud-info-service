# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

import json
import pytest
import requests

def test_root_request(baseurl):
    url = baseurl
    resp = requests.get(url, allow_redirects=False, verify=False)
    expected_status_code = 301
    assert resp.status_code == expected_status_code
    assert 'https://www.suse.com/solutions/public-cloud/' == resp.headers['Location']

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_providers(baseurl, extension):
    url = baseurl + '/v1/providers' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    assert "providers" in resp.text
    assert "amazon" in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_types(baseurl, provider, extension):
    url = baseurl + '/v1/' + provider + '/servers/types' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    #until pint-ng goes live
    if 'susepubliccloudinfo.suse.com' in baseurl:
        assert "smt" in resp.text
        assert "regionserver" in resp.text
    else:
        if provider == 'amazon' or provider == 'google' or 'provider' == 'microsoft':
            assert "region" in resp.text
            assert "update" in resp.text
        if provider == 'alibaba' or provider == 'oracle':
            assert "smt" in resp.text
            assert "regionserver" in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_get_image_states(baseurl, extension):
    url = baseurl + '/v1/images/states' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    assert "states" in resp.text
    expected_states = ['active','inactive','deprecated','deleted']
    validate(resp, expected_status_code, extension)
    for state in expected_states:
        assert state in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_regions(baseurl, provider, extension):
    url = baseurl + '/v1/' + provider + '/regions' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    assert "regions" in resp.text
    if provider == 'alibaba':
        assert "ap-northeast-1" in resp.text
    if provider == 'amazon':
        assert "us-east-2" in resp.text
    if provider == 'google':
        assert "us-east1" in resp.text
    if provider == 'microsoft':
        assert "useast" in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_for_region_and_type(baseurl, provider, extension):
    server_types = requests.get(baseurl + '/v1/' + provider + 'servers/types')
    regions = requests.get(baseurl + '/v1/' + provider + '/regions', verify=False)
    for region in json.loads(regions.content)['regions']:
        for server_type in server_types:
            url = baseurl + '/v1/' + provider + '/' + region['name'] + '/servers/' + server_type +  extension
            resp = requests.get(url, verify=False)
            expected_status_code = 200
            validate(resp, expected_status_code, extension)
            assert region in resp.text
            assert server_type in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_for_type(baseurl, provider, extension):
    server_types = requests.get(baseurl + '/v1/' + provider + 'servers/types')
    for server_type in server_types:
        url = baseurl + '/v1/' + provider + '/servers/' + server_type + extension
        resp = requests.get(url, verify=False)
        expected_status_code = 200
        validate(resp, expected_status_code, extension)
        assert server_type in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_for_region_and_state(baseurl, provider, extension):
    img_states = requests.get(baseurl + '/v1/' + provider + '/images/states')
    regions = requests.get(baseurl + '/v1/' + provider + '/regions', verify=False)
    for region in json.loads(regions.content)['regions']:
        for img_state in img_states:
            url = baseurl + '/v1/' + provider + '/' + region[
                'name'] + '/images/' + img_state + extension
            resp = requests.get(url, verify=False)
            expected_status_code = 200
            validate(resp, expected_status_code, extension)
            assert img_state in resp.text
            assert region in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_for_state(baseurl, provider, extension):
    img_states = requests.get(baseurl + '/v1/' + provider + '/images/states')
    for img_state in img_states:
        url = baseurl + '/v1/' + provider + '/images/' + img_state + extension
        resp = requests.get(url, verify=False)
        expected_status_code = 200
        validate(resp, expected_status_code, extension)
        assert img_state in resp.text
        assert "images" in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("category", ['images', 'servers'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'oracle']) #microsoft will be covered in another test
def test_get_provider_region_category(baseurl, provider, category, extension):
        regions_resp = requests.get(baseurl + '/v1/' + provider + '/regions', verify=False)
        regions = json.loads(regions_resp.content)['regions']
        if len(regions) != 0:
            # Pick the first region.. no need to iterate with all the regions
            region = regions[0]
            url = baseurl + '/v1/' + provider + '/' + region[
                'name'] + '/' + category + extension
            resp = requests.get(url, verify=False)
            expected_status_code = 200
            validate(resp, expected_status_code, extension)
            if extension != '.xml' and len(json.loads(resp.content)[category]) != 0:
                assert region['name'] in resp.text
            assert category in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("category", ['images', 'servers'])
def test_get_microsoft_region_servers(baseurl, category, extension):
    microsofttestregions = ['australiacentral', 'australiacentral2',
                            'Brazil South', 'brazilsouth',
                            'canadaeast', 'centralus', 'centraluseuap','chinaeast',
                            'East US', 'eastus',
                            'francecentral', 'francesouth',
                            'Germany Central', 'germanycentral',
                            'japaneast', 'japanwest',
                            'northcentralus', 'northeurope',
                            'Southeast Asia', 'southeastasia',
                            'uaecentral', 'uknorth', 'uksouth', 'uksouth2',
                            'usgovarizona', 'usgoviowa', 'usgovtexas', 'usgovvirginia',
                            'West Europe', 'westeurope', 'westindia', 'West US','westus', 'westus2', 'westus3'
                        ]
    for region_name in microsofttestregions:
        url = baseurl + '/v1/microsoft/' + region_name + '/' + category +  extension
        resp = requests.get(url, verify=False)
        expected_status_code = 200
        validate(resp, expected_status_code, extension)
        if extension != '.xml' and len(json.loads(resp.content)[category]) != 0:
            assert region_name in resp.text
        assert category in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("category", ['images', 'servers'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_provider_category(baseurl, provider, category, extension):
    url = baseurl + '/v1/' + provider + '/' + category + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    assert category in resp.text

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("category", ['images', 'servers'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_category_data_version(baseurl, provider, category, extension):
    #skip until new pint-ng is available in susepubliccloudinfo.suse.com
    if 'susepubliccloudinfo.suse.com' in baseurl:
        pytest.skip("vsersions api not available in susepubliccloudinfo.suse.com")
    else:
        url = baseurl + '/v1/' + provider + '/dataversion' + extension + '?category=' + category
        resp = requests.get(url, verify=False)
        if category == 'servers' and (provider == 'alibaba' or provider == 'oracle'):
            expected_status_code = 404
            validate(resp, expected_status_code, extension)
        else:
            expected_status_code = 200
            validate(resp, expected_status_code, extension)

#negative tests
@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("category", ['images', 'servers'])
def test_get_invalid_provider_category(baseurl, category, extension):
    invalid_provider = 'foo'
    url = baseurl + '/v1/' + invalid_provider + '/' + category + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 404
    validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_for_invalid_server_type(baseurl, provider, extension):
    invalid_server_type='foo'
    url = baseurl + '/v1/' + provider + '/servers/' + invalid_server_type + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 404
    validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_for_invalid_image_state(baseurl, provider, extension):
    invalid_image_state ='foo'
    url = baseurl + '/v1/' + provider + '/images/' + invalid_image_state + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 404
    validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_for_region_and_invalid_server_type(baseurl, provider, extension):
    regions_resp = requests.get(baseurl + '/v1/' + provider + '/regions', verify=False)
    regions = json.loads(regions_resp.content)['regions']
    invalid_server_type = 'foo'
    if len(regions) != 0:
        region = regions[0] #pick the first region
        url = baseurl + '/v1/' + provider + '/' + region ['name'] + '/servers/' + invalid_server_type +  extension
        resp = requests.get(url, verify=False)
        expected_status_code = 404
        validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_for_region_and_invalid_image_state(baseurl, provider, extension):
    invalid_image_state='foo'
    regions_resp = requests.get(baseurl + '/v1/' + provider + '/regions', verify=False)
    regions = json.loads(regions_resp.content)['regions']
    if len(regions) != 0:
        region = regions[0] #pick the first region
        url = baseurl + '/v1/' + provider + '/' + region[
            'name'] + '/images/' + invalid_image_state + extension
        resp = requests.get(url, verify=False)
        expected_status_code = 404
        validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("category", ['images', 'servers'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_invalid_region_category(baseurl, provider, category, extension):
    invalid_region='foo'
    url = baseurl + '/v1/' + provider + '/' + invalid_region + '/' + category + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 404
    validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("category", ['images', 'servers'])
def test_provider_category_invalid_extension(baseurl, category):
    invalid_extension = '.foo'
    provider='amazon'
    url = baseurl + '/v1/' + provider + '/' + category + invalid_extension
    resp = requests.get(url, verify=False)
    assert resp.status_code == 400

@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
def test_unsupported_version(baseurl, extension):
    # test v2
    provider = 'amazon'
    url = baseurl + '/v2/' + provider + '/images' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 400
    validate(resp, expected_status_code, extension)

def validate(resp, expected_status, extension):
    assert resp.status_code == expected_status  # actual_status == expected_status
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
    if expected_status == 200:
        if extension == '.xml':
            assert resp.headers['Content-Type'] == "application/xml;charset=utf-8"
            assert '<?xml version=' in resp.content.decode('utf-8')
        else:
            assert resp.headers['Content-Type'] == 'application/json'
            assert '{' in resp.content.decode('utf-8')
    else:
        # For 400, 404 content-type is set to text/html
        #conttype = 'text/html;charset=utf-8'
        #newconttype = 'text/html; charset=utf-8'
        assert 'text/html' in resp.headers['Content-Type']
        assert len(resp.content) == 0
