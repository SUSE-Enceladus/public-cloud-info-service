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
import gzip
import io


# For some providers we need to remap the server type returned by
# the v1/providers/servers/types request to the corresponding field
# name that will appear in the servers list
_STYPE_REMAP = dict(update="smt", region="regionserver")
_PROVIDER_STYPE_REMAP = dict(
    amazon=_STYPE_REMAP,
    google=_STYPE_REMAP,
    microsoft=_STYPE_REMAP,
)


#
# Helper functions for retrieving data via the API to support
# testing efforts.
#

def _get_provider_server_types_list(baseurl, provider):
    server_types_resp = requests.get(baseurl + '/v1/' + provider + '/servers/types',
                                     verify=False)

    # validate that the provider server types query worked
    validate(server_types_resp, 200, '')

    # extract the list of server types from the response
    return [s['name'] for s in server_types_resp.json()['types']]


def _get_provider_regions_list(baseurl, provider):
    regions_resp = requests.get(baseurl + '/v1/' + provider + '/regions',
                                verify=False)

    # validate that the provider regions query worked
    validate(regions_resp, 200, '')

    # extract the list of regions from the response
    return [r['name'] for r in regions_resp.json()['regions']]


def _get_image_states_list(baseurl):
    img_states_resp = requests.get(baseurl + '/v1/images/states',
                                   verify=False)

    # validate that the image states query worked
    validate(img_states_resp, 200, '')

    # extract the list of images states from the response
    return [s['name'] for s in img_states_resp.json()['states']]


def _get_provider_region_images_in_state(baseurl, provider, region, state):
    url = baseurl + '/v1/' + provider
    # if a non-empty region was provided, add it to the URL
    if region:
        url += '/' + region
    url += '/images/' + state

    images_resp = requests.get(url, verify=False)

    # validate that the images query worked
    validate(images_resp, 200, '')

    return [i["name"] for i in images_resp.json()['images']]


def _decompress_gzip(resp):
    with gzip.GzipFile(fileobj=io.BytesIO(resp.content), mode='rb') as f:
        uncompressed_data = f.read()
    return uncompressed_data

def _get_response_content(resp, extension):
    if '.gz' in extension:
        resp_content = _decompress_gzip(resp).decode('utf-8')
        if '.xml' in extension:
            assert '<?xml version=' in resp_content
        else:
            assert '{' in resp_content
    else:
        resp_content = resp.text
    return resp_content    


#
# Helper functions for validating the data
#

def _provider_server_type_name(provider, server_type):
    # return the remap'd server_type name, or server_type if
    # not remapped for that provider.
    return _PROVIDER_STYPE_REMAP.get(provider, {}).get(
                server_type, server_type)


#
# Tests
#

def test_root_request(baseurl):
    url = baseurl
    resp = requests.get(url, allow_redirects=False, verify=False)
    expected_status_code = 301
    assert resp.status_code == expected_status_code
    assert 'https://www.suse.com/solutions/public-cloud/' == resp.headers['Location']

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
def test_get_providers(baseurl, extension):
    url = baseurl + '/v1/providers' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    resp_text = _get_response_content(resp, extension)
    assert "providers" in resp_text 
    assert "amazon" in resp_text

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_types(baseurl, provider, extension):
    url = baseurl + '/v1/' + provider + '/servers/types' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    
    resp_text = _get_response_content(resp, extension)
    if provider in ['amazon', 'google', 'microsoft']:
        assert "region" in resp_text
        assert "update" in resp_text
    if provider in ['alibaba', 'oracle']:
        assert "smt" in resp_text
        assert "regionserver" in resp_text

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
def test_get_image_states(baseurl, extension):
    url = baseurl + '/v1/images/states' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    resp_text = _get_response_content(resp, extension)
    assert "states" in resp_text
    expected_states = ['active','inactive','deprecated','deleted']
    for state in expected_states:
        assert state in resp_text

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_regions(baseurl, provider, extension):
    url = baseurl + '/v1/' + provider + '/regions' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    resp_text = _get_response_content(resp, extension)
    assert "regions" in resp_text
    if provider == 'alibaba':
        assert "ap-northeast-1" in resp_text
    if provider == 'amazon':
        assert "us-east-2" in resp_text
    if provider == 'google':
        assert "us-east1" in resp_text
    if provider == 'microsoft':
        assert "useast" in resp_text


@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_for_region_and_type(baseurl, provider, extension):
    server_types = _get_provider_server_types_list(baseurl, provider)
    regions = _get_provider_regions_list(baseurl, provider)

    for region in regions:
        for server_type in server_types:
            url = baseurl + '/v1/' + provider + '/' + region + '/servers/' + server_type +  extension
            resp = requests.get(url, verify=False)
            print(url)
            expected_status_code = 200
            validate(resp, expected_status_code, extension)
            resp_text = _get_response_content(resp, extension)
            print(resp_text)
            # only check for the server type in the resp.text if
            # there are actually servers in the response.
            if (('.xml' in extension) and ("<servers/>" not in resp_text) or
                ('.xml' not in extension) and json.loads(resp_text)['servers']):
                assert _provider_server_type_name(provider, server_type) in resp_text
                # for Azure regions can have multiple names, but only the
                # one of the possible names will appear in the servers entry
                # and there isn't an easy way to remap the region name that
                # we are testing to the one that will appear in the servers
                # entry.
                if provider != 'microsoft':
                    assert region in resp_text


@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_for_type(baseurl, provider, extension):
    server_types = _get_provider_server_types_list(baseurl, provider)

    for server_type in server_types:
        url = baseurl + '/v1/' + provider + '/servers/' + server_type + extension
        resp = requests.get(url, verify=False)
        expected_status_code = 200
        validate(resp, expected_status_code, extension)
        resp_text = _get_response_content(resp, extension)
        print(resp_text)
        assert "servers" in resp_text

        # only check for the server type in the resp.text if
        # there are actually servers in the response.
        if (('.xml' in extension) and ("<servers/>" not in resp_text) or
            ('.xml' not in extension) and json.loads(resp_text)['servers']):
            assert _provider_server_type_name(provider, server_type) in resp_text

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_for_region_and_state(baseurl, provider, extension):
    img_states = _get_image_states_list(baseurl)
    regions = _get_provider_regions_list(baseurl, provider)

    for region in regions:
        for img_state in img_states:
            url = (baseurl + '/v1/' + provider + '/' + region +
                   '/images/' + img_state + extension)
            resp = requests.get(url, verify=False)
            expected_status_code = 200
            validate(resp, expected_status_code, extension)
            resp_text = _get_response_content(resp, extension)
            assert "images" in resp_text

            # only check for the img_state and region in the resp.text if
            # there are actually images in the response.
            if (('.xml' in extension) and ("<images/>" not in resp_text) or
                ('.xml' not in extension) and json.loads(resp_text)['images']):
                assert img_state in resp_text
                if provider not in ['google']:
                    assert region in resp_text


@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_for_state(baseurl, provider, extension):
    img_states = _get_image_states_list(baseurl)

    for img_state in img_states:
        url = baseurl + '/v1/' + provider + '/images/' + img_state + extension
        resp = requests.get(url, verify=False)
        expected_status_code = 200
        validate(resp, expected_status_code, extension)
        resp_text = _get_response_content(resp, extension)
        assert "images" in resp_text
        # only check for the img_state in the resp.text if
        # there are actually images in the response.
        if (('.xml' in extension) and ("<images/>" not in resp_text) or
            ('.xml' not in extension) and json.loads(resp_text)['images']):
            assert img_state in resp_text


@pytest.mark.parametrize("extension", ['', '.json', '.xml'])
@pytest.mark.parametrize("category", ['images', 'servers'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'oracle']) #microsoft will be covered in another test
def test_get_provider_region_category(baseurl, provider, category, extension):
    regions = _get_provider_regions_list(baseurl, provider)

    if len(regions) != 0:
        # Pick the first region.. no need to iterate with all the regions
        region = regions[0]
        url = baseurl + '/v1/' + provider + '/' + region + '/' + category + extension
        print(url)
        resp = requests.get(url, verify=False)
        expected_status_code = 200
        validate(resp, expected_status_code, extension)
        resp_text = _get_response_content(resp, extension)
        
        if ('.xml' not in extension) and len(json.loads(resp_text)[category]) != 0:
            assert region in resp_text
        assert category in resp_text

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.xml.gz', '.json.gz'])
@pytest.mark.parametrize("category", ['images', 'servers'])
def test_get_microsoft_region_servers(baseurl, category, extension):
    microsofttestregions = ['australiacentral', 'australiacentral2',
                            'Brazil South', 'brazilsouth',
                            'canadaeast', 'centralus', 'centraluseuap','chinaeast',
                            'East US', 'eastus',
                            'francecentral', 'francesouth',
                            'germanycentral',
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
        resp_text = _get_response_content(resp, extension)
        if ('.xml' not in extension) and len(json.loads(resp_text)[category]) != 0:
            assert region_name in resp_text
        assert category in resp_text

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("category", ['images', 'servers'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_provider_category(baseurl, provider, category, extension):
    url = baseurl + '/v1/' + provider + '/' + category + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)
    resp_text = _get_response_content(resp, extension)
    assert category in resp_text

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("category", ['images', 'servers'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_category_data_version(baseurl, provider, category, extension):
    url = baseurl + '/v1/' + provider + '/dataversion' + extension + '?category=' + category
    resp = requests.get(url, verify=False)
    if category == 'servers' and (provider == 'alibaba' or provider == 'oracle'):
        expected_status_code = 404
        validate(resp, expected_status_code, extension)
    else:
        expected_status_code = 200
        validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", [''])
def test_get_psql_server_version(baseurl, extension):
    url = baseurl + '/db-server-version'
    resp = requests.get(url, verify=False)
    expected_status_code = 200
    validate(resp, expected_status_code, extension)


@pytest.mark.parametrize("date", ['20191231', '20201231', '20211231', '20221231'])
@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_deletedby(baseurl, provider, date, extension):
    # include an empty region entry to test the non-regioned API as well
    regions = [''] + _get_provider_regions_list(baseurl, provider)

    for region in regions:
        # construct request URL optionally including region if not empty
        url = baseurl + '/v1/' + provider
        if region:
            url += '/' + region
        url += '/images/deletedby/' + date + extension

        resp = requests.get(url, verify=False)
        expected_status_code = 200
        validate(resp, expected_status_code, extension)
        resp_text = _get_response_content(resp, extension)
        assert "images" in resp_text
        # only check for the deprecated on field in the resp.text if
        # there are actually images in the response.
        if (('.xml' in extension) and ("<images/>" not in resp_text) or
            ('.xml' not in extension) and ("['images']" in resp_text)):
            assert 'deprecatedon' in resp_text


@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_deletiondate(baseurl, provider, extension):
    img_states = _get_image_states_list(baseurl)

    # include an empty region entry to test the non-regioned API as well
    regions = [''] + _get_provider_regions_list(baseurl, provider)

    for region in regions:
        for state in img_states:
            images = _get_provider_region_images_in_state(baseurl, provider, region, state)

            # If no images were found for provider/region combo
            if not images:
                continue

            # Just test the first image, not all images
            image = images[0]

            # construct request URL optionally including region if not empty
            url = baseurl + '/v1/' + provider
            if region:
                url += '/' + region
            url += '/images/deletiondate/' + image + extension

            resp = requests.get(url, verify=False)
            expected_status_code = 200
            validate(resp, expected_status_code, extension)
            resp_text = _get_response_content(resp, extension)
            assert "deletiondate" in resp_text

            if state in ['deprecated', 'deleted']:
                if ('.xml' in extension):
                    assert "<deletiondate>" in resp_text
                    assert "</deletiondate>" in resp_text
                else:
                    assert json.loads(resp_text)['deletiondate'] != ""
            elif region:
                # skip provider level check as sometimes images can be in more
                # than one state across provider regions.
                if ('.xml' in extension):
                    assert "<deletiondate/>" in resp_text
                else:
                    assert json.loads(resp_text)['deletiondate'] == ""


#negative tests
@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("category", ['images', 'servers'])
def test_get_invalid_provider_category(baseurl, category, extension):
    invalid_provider = 'foo'
    url = baseurl + '/v1/' + invalid_provider + '/' + category + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 404
    validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_for_invalid_server_type(baseurl, provider, extension):
    invalid_server_type='foo'
    url = baseurl + '/v1/' + provider + '/servers/' + invalid_server_type + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 404
    validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_for_invalid_image_state(baseurl, provider, extension):
    invalid_image_state ='foo'
    url = baseurl + '/v1/' + provider + '/images/' + invalid_image_state + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 404
    validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_servers_for_region_and_invalid_server_type(baseurl, provider, extension):
    regions = _get_provider_regions_list(baseurl, provider)
    invalid_server_type = 'foo'
    if len(regions) != 0:
        region = regions[0] #pick the first region
        url = baseurl + '/v1/' + provider + '/' + region + '/servers/' + invalid_server_type +  extension
        resp = requests.get(url, verify=False)
        expected_status_code = 404
        validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
@pytest.mark.parametrize("provider", ['alibaba', 'amazon', 'google', 'microsoft', 'oracle'])
def test_get_provider_images_for_region_and_invalid_image_state(baseurl, provider, extension):
    invalid_image_state='foo'
    regions = _get_provider_regions_list(baseurl, provider)
    if len(regions) != 0:
        region = regions[0] #pick the first region
        url = (baseurl + '/v1/' + provider + '/' + region
               + '/images/' + invalid_image_state + extension)
        resp = requests.get(url, verify=False)
        expected_status_code = 404
        validate(resp, expected_status_code, extension)

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
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

@pytest.mark.parametrize("extension", ['', '.json', '.xml', '.gz', '.json.gz', '.xml.gz'])
def test_unsupported_version(baseurl, extension):
    # test v2
    provider = 'amazon'
    url = baseurl + '/v2/' + provider + '/images' + extension
    resp = requests.get(url, verify=False)
    expected_status_code = 400
    validate(resp, expected_status_code, extension)


def test_get_images_deletedby_no_date(baseurl):
    provider = 'amazon'
    date = ''
    extension = ''
    expected_status_code = 400

    url = baseurl + '/v1/' + provider + '/images/deletedby/' + date + extension
    resp = requests.get(url, verify=False)
    validate(resp, expected_status_code, extension)


@pytest.mark.parametrize("date", ['1', '11', '111', '1111', '11111', '111111',
                                  '1111111', '99999999', '20230431', '200231231'])
def test_get_images_deletedby_invalid_date(baseurl, date):
    provider = 'amazon'
    extension = ''
    expected_status_code = 404

    url = baseurl + '/v1/' + provider + '/images/deletedby/' + date + extension
    resp = requests.get(url, verify=False)
    validate(resp, expected_status_code, extension)


def test_get_images_deletiondate_no_image(baseurl):
    provider = 'amazon'
    image = ''
    extension = ''
    expected_status_code = 400

    url = baseurl + '/v1/' + provider + '/images/deletiondate/' + image + extension
    resp = requests.get(url, verify=False)
    validate(resp, expected_status_code, extension)


def test_get_images_deletiondate_invalid_image(baseurl):
    provider = 'amazon'
    image = 'foo'
    extension = ''
    expected_status_code = 404

    url = baseurl + '/v1/' + provider + '/images/deletiondate/' + image + extension
    resp = requests.get(url, verify=False)
    validate(resp, expected_status_code, extension)


def validate(resp, expected_status, extension):
    assert resp.status_code == expected_status  # actual_status == expected_status
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
    if expected_status == 200:
        if '.gz' in extension:
            assert resp.headers['Content-Type'] == "application/gzip;charset=utf-8"
        elif extension == '.xml':
            assert resp.headers['Content-Type'] == "application/xml;charset=utf-8"
            assert '<?xml version=' in resp.content.decode('utf-8')
        else:
            assert resp.headers['Content-Type'] == "application/json;charset=utf-8"
            assert '{' in resp.content.decode('utf-8')
    else:
        # For 400, 404 content-type is set to text/html
        #conttype = 'text/html;charset=utf-8'
        #newconttype = 'text/html; charset=utf-8'
        assert 'text/html' in resp.headers['Content-Type']
        assert len(resp.content) == 0
