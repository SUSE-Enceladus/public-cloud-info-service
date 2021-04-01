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

def construct_mock_expected_response(content_dict, collection_name):
    if collection_name:
        content = {collection_name: content_dict}
    else:
        content = content_dict
    return content

query_providers_return_value = ['amazon', 'microsoft', 'google', 'alibaba', 'oracle']
expected_json_providers = {'providers': [
    {'name': 'amazon'},{'name': 'microsoft'},{'name': 'google'},{'name': 'alibaba'},{'name': 'oracle'}
    ]
}

mocked_return_value_server_types = ['region', 'update']
expected_json_server_types = {'types': ['region', 'update']}

mocked_return_value_images = {}
expected_json_images = {}

mocked_return_value_servers = {}
expected_json_servers = {}

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
