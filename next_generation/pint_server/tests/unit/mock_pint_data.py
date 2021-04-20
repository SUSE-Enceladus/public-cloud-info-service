import glob
import os

from lxml import etree

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
