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

from collections import namedtuple
import glob
import os
import datetime

from lxml import etree

from pint_server.models import ImageState


DATE_FORMAT = '%Y%m%d'


def get_datetime_date(date):
    return datetime.datetime.strptime(date, DATE_FORMAT)


def images(provider):
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_file = glob.glob(base_path + '/mockpintdata/' + provider + '.xml')
    content = open(data_file[0]).readlines()
    content = ''.join(content[1:])
    root = etree.fromstring(content)
    images = root.findall('images')[0]
    image_list = []
    for image in images:
        image_list.append(dict(image.attrib))
    return image_list


def servers(provider):
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_file = glob.glob(base_path + '/mockpintdata/' + provider + '.xml')
    content = open(data_file[0]).readlines()
    content = ''.join(content[1:])
    root = etree.fromstring(content)
    servers = root.findall('servers')[0]
    server_list = []
    for server in servers:
        server_list.append(dict(server.attrib))
    return server_list

def filter_mocked_return_value_servers_by_type(servers, type):
    srv_list = []
    for server in servers:
        if server.get('type') == type:
            srv_list.append(server)
    return srv_list

def filter_mocked_return_value_images_by_state(images, img_state):
    img_list = []
    for image in images:
        if image.get('state') == img_state:
            img_list.append(image)
    return img_list

def filter_mocked_return_value_images_region(images, region):
    img_list = []
    for image in images:
        if image.get('region') == region:
            img_list.append(image)
    return img_list

def filter_mocked_return_value_servers_region(servers, region):
    srv_list = []
    for server in servers:
        if server.get('region') == region:
            srv_list.append(server)
    return srv_list

def construct_mock_expected_response(content_dict, collection_name):
    if collection_name:
        content = {collection_name: content_dict}
    else:
        content = content_dict
    return content

get_supported_providers_return_value = ['amazon', 'microsoft', 'google', 'alibaba', 'oracle']
expected_json_providers = {'providers': [
    {'name': 'amazon'},{'name': 'microsoft'},{'name': 'google'},{'name': 'alibaba'},{'name': 'oracle'}
    ]
}

mocked_return_value_image_states = [{"name":"active"},{"name":"deleted"},{"name":"deprecated"},{"name":"inactive"}]
expected_json_image_states = {"states":[{"name":"active"},{"name":"deleted"},{"name":"deprecated"},{"name":"inactive"}]}

mocked_return_value_server_types = [{"name": "region"},{"name": "update"}]
expected_json_server_types = {'types': [{'name': 'region'}, {'name': 'update'}]}

mocked_return_value_images = {}
expected_json_images = {}

mocked_return_value_servers = {}
expected_json_servers = {}

mocked_return_value_regions = {}
expected_json_regions = {}

#Images
mocked_return_value_images['alibaba'] = images('alibaba')
expected_json_images['alibaba'] = construct_mock_expected_response(mocked_return_value_images['alibaba'] , 'images')

mocked_return_value_images['amazon'] = images('amazon')
expected_json_images['amazon'] = construct_mock_expected_response(mocked_return_value_images['amazon'] , 'images')

mocked_return_value_images['google'] = images('google')
expected_json_images['google'] = construct_mock_expected_response(mocked_return_value_images['google'] , 'images')

mocked_return_value_images['microsoft'] = images('microsoft')
expected_json_images['microsoft'] = construct_mock_expected_response(mocked_return_value_images['microsoft'] , 'images')

mocked_return_value_images['oracle'] = images('oracle')
expected_json_images['oracle'] = construct_mock_expected_response(mocked_return_value_images['oracle'] , 'images')

#Servers
mocked_return_value_servers['alibaba'] = servers('alibaba')
expected_json_servers['alibaba'] = construct_mock_expected_response(mocked_return_value_servers['alibaba'] , 'servers')

mocked_return_value_servers['amazon'] = servers('amazon')
expected_json_servers['amazon'] = construct_mock_expected_response(mocked_return_value_servers['amazon'] , 'servers')

mocked_return_value_servers['google'] = servers('google')
expected_json_servers['google'] = construct_mock_expected_response(mocked_return_value_servers['google'] , 'servers')

mocked_return_value_servers['microsoft'] = servers('microsoft')
expected_json_servers['microsoft'] = construct_mock_expected_response(mocked_return_value_servers['microsoft'] , 'servers')

mocked_return_value_servers['oracle'] = servers('oracle')
expected_json_servers['oracle'] = construct_mock_expected_response(mocked_return_value_servers['oracle'] , 'servers')

#Regions
mocked_return_value_regions['alibaba'] = [{'name': 'ap-south-1'},{ 'name': 'us-west-1' }]
expected_json_regions['alibaba'] = {"regions":[{'name': 'ap-south-1'},{ 'name': 'us-west-1' }]}

mocked_return_value_regions['amazon'] = [{'name': 'ap-southeast-2'},{'name': 'ap-south-1'},{'name': 'us-west-1'}]
expected_json_regions['amazon'] = {"regions":[{'name': 'ap-southeast-2'},{'name': 'ap-south-1'},{'name': 'us-west-1'}]}

mocked_return_value_regions['google'] = [{'name': 'asia-east1'},{'name': 'asia-northeast1'},{'name': 'asia-south1'}, {'name': 'us-west1'}]
expected_json_regions['google'] = {"regions":[{'name': 'asia-east1'},{'name': 'asia-northeast1'},{'name': 'asia-south1'}, {'name': 'us-west1'}]}

mocked_return_value_regions['microsoft'] = [{'name': 'West US'},{'name': 'Southeast Asia'},{'name': 'southeastasia'}, {'name': 'asiasoutheast'},{'name': 'westus'}, {'name': 'uswest'}]
expected_json_regions['microsoft'] = {"regions":[{'name': 'West US'},{'name': 'Southeast Asia'},{'name': 'southeastasia'}, {'name': 'asiasoutheast'},{'name': 'westus'}, {'name': 'uswest'}]}

mocked_return_value_regions['oracle'] = []
expected_json_regions['oracle'] = {"regions":[]}

#
# /v1/<provider>/images/deletiondate/<image> testing
#

MockDeletionDateImage = namedtuple("MockDeletionDateImage",
                                   " ".join(["state",
                                             "deprecatedon",
                                             "deletedon"]))

# Need to emulate the list of images returned by a DB query,
# supporting iteration and a count method.
class MockDBImagesQuery:
    def __init__(self, images=None):
        if images is None:
            images = []
        self.images = images

    def __iter__(self):
        return iter(self.images)

    def count(self):
        return len(self.images)

    def __str__(self):
        return "".join([
            "[",
            ", ".join([str(i) for i in self.images]),
            "]"
        ])

    def __repr__(self):
        return "".join([
            f"{self.__class__.__name__}(images=[",
            ", ".join([str(i) for i in self.images]),
            "])"
        ])


# Create a table of mocked images lists, one per test image
# name, that can be used as the mocked return value for the
# pint_server.app.query_image_in_provider_region() call
_deprecatedon_date = get_datetime_date('20220101')
_deletedon_date = get_datetime_date('20220701')
_mock_deletiondate_active_image = MockDeletionDateImage(
    state=ImageState.active,
    deprecatedon='',
    deletedon='',
)
_mock_deletiondate_inactive_image = MockDeletionDateImage(
    state=ImageState.inactive,
    deprecatedon='',
    deletedon='',
)
_mock_deletiondate_deprecated_image = MockDeletionDateImage(
    state=ImageState.deprecated,
    deprecatedon=_deprecatedon_date,
    deletedon='',
)
_mock_deletiondate_deleted_image = MockDeletionDateImage(
    state=ImageState.deleted,
    deprecatedon=_deprecatedon_date,
    deletedon=_deletedon_date,
)
mocked_deletiondate_images = {
    # test images in the active state
    "image1": MockDBImagesQuery(images=[
        _mock_deletiondate_active_image,
    ]),
    # test images in the inactive state
    "image2": MockDBImagesQuery(images=[
        _mock_deletiondate_inactive_image,
    ]),
    # test images in the deprecated state
    "image3": MockDBImagesQuery(images=[
        _mock_deletiondate_deprecated_image,
    ]),
    # test images in the deleted state
    "image4": MockDBImagesQuery(images=[
        _mock_deletiondate_deleted_image,
    ]),
    # test images in mixed active and deprecated states
    "image5": MockDBImagesQuery(images=[
        _mock_deletiondate_active_image,
        _mock_deletiondate_deprecated_image,
    ]),
    # test images in mixed inactive and deleted states
    "image6": MockDBImagesQuery(images=[
        _mock_deletiondate_inactive_image,
        _mock_deletiondate_deleted_image,
    ]),
}

# expected response for providers with 6 months deletion policy
_mocked_6months_deletiondates = {
        'image1': '',
        'image2': '',
        'image3': '20220701',
        'image4': '20220701',
        'image5': '20220701',
        'image6': '20220701',
}

# expected response for providers with 2 years deletion policy
_mocked_2years_deletiondates = {
        'image1': '',
        'image2': '',
        'image3': '20240101',
        'image4': '20220701',
        'image5': '20240101',
        'image6': '20220701',
}

# provider specific expected deletiondate responses for above
# list of mock images.
mocked_expected_deletiondate = {
    'alibaba': _mocked_6months_deletiondates,
    'amazon': _mocked_2years_deletiondates,
    'google': _mocked_6months_deletiondates,
    'microsoft': _mocked_6months_deletiondates,
    'oracle': _mocked_6months_deletiondates,
}
