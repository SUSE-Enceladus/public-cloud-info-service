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

import datetime
import re
from decimal import Decimal
from flask import (abort, Flask, jsonify, make_response, request, redirect,
                   Response)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, or_
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from xml.dom import minidom
import xml.etree.ElementTree as ET

from pint_server.database import init_db
from pint_server.models import (ImageState, AmazonImagesModel,
                                OracleImagesModel, AlibabaImagesModel,
                                MicrosoftImagesModel, GoogleImagesModel,
                                AmazonServersModel, MicrosoftServersModel,
                                GoogleServersModel, ServerType,
                                VersionsModel, MicrosoftRegionMapModel)


app = Flask(__name__)
db_session = init_db()

cors_config = {
    "origins": ["*"]
}
CORS(app, resources={
    r"/*": cors_config
})

# we don't care about modifications as we are doing DB read only
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

null_to_empty = lambda s : s or ''


REGIONSERVER_SMT_MAP = {
    'smt': 'update',
    'regionserver': 'region',
    'update': 'update',
    'region': 'region'
}

PROVIDER_IMAGES_MODEL_MAP = {
    'amazon': AmazonImagesModel,
    'google': GoogleImagesModel,
    'microsoft': MicrosoftImagesModel,
    'alibaba': AlibabaImagesModel,
    'oracle': OracleImagesModel
}

PROVIDER_SERVERS_MODEL_MAP = {
    'amazon': AmazonServersModel,
    'google': GoogleServersModel,
    'microsoft': MicrosoftServersModel
}

SUPPORTED_CATEGORIES = ['images', 'servers']


def get_supported_providers():
    versions  = VersionsModel.query.with_entities(VersionsModel.tablename)
    return list({re.sub('(servers|images)', '', v.tablename) for v in versions})


def get_providers():
    """Get all the providers"""
    return [{'name': provider} for provider in get_supported_providers()]


def json_to_xml(json_obj, collection_name, element_name):
    if collection_name:
        root = ET.Element(collection_name)
        for dict in json_obj:
            ET.SubElement(root, element_name, dict)
    else:
        if element_name:
            root = ET.Element(element_name, json_obj)
        else:
            # NOTE(gyee): if neither collection_name and element_name are
            # specified, we assume the json_obj has a single key value pair
            # with key as the tag and value as the text
            tag = list(json_obj.keys())[0]
            root = ET.Element(tag)
            root.text = json_obj[tag]
    parsed = minidom.parseString(
        ET.tostring(root, encoding='utf8', method='xml'))
    return parsed.toprettyxml(indent='  ')


def get_formatted_dict(obj, extra_attrs=None, exclude_attrs=None):
    obj_dict = {}
    for attr in obj.__dict__.keys():
        if exclude_attrs and attr in exclude_attrs:
            continue
        elif attr[0] == '_':
            continue
        else:
            value = obj.__dict__[attr]
            if isinstance(value, Decimal):
                obj_dict[attr] = float(value)
            elif isinstance(value, ImageState):
                obj_dict[attr] = obj.state.value
            elif isinstance(value, ServerType):
                obj_dict[attr] = obj.type.value
            elif isinstance(value, datetime.date):
                obj_dict[attr] = value.strftime('%Y%m%d')
            else:
                obj_dict[attr] = null_to_empty(value)
    if extra_attrs:
        obj_dict.update(extra_attrs)
    return obj_dict


def get_provider_servers_for_type(provider, server_type):
    servers = []
    if server_type not in REGIONSERVER_SMT_MAP:
        abort(Response('', status=404))    
    mapped_server_type = REGIONSERVER_SMT_MAP[server_type]
    server_types_json = get_provider_servers_types(provider)
    server_types = [t['name'] for t in server_types_json]
    if (PROVIDER_SERVERS_MODEL_MAP.get(provider) != None and
            mapped_server_type in server_types):
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
            PROVIDER_SERVERS_MODEL_MAP[provider].type == mapped_server_type)
        return [get_formatted_dict(server) for server in servers]
    else:
        abort(Response('', status=404))


def get_provider_servers_types(provider):
    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.distinct(
            PROVIDER_SERVERS_MODEL_MAP[provider].type)
        return [{'name': server.type.value} for server in servers]
    else:
        # NOTE(gyee): currently we don't have DB tables for both Alibaba and
        # Oracle servers. In order to maintain compatibility with the
        # existing Pint server, we are returning the original server
        # types. In the future, if we do decide to create the tables,
        # then we can easily add them to PROVIDER_SERVERS_MODEL_MAP.
        return [{'name': 'smt'}, {'name': 'regionserver'}]


def get_provider_regions(provider):
    if provider == 'microsoft':
        return _get_all_azure_regions()

    servers = []
    images = []
    region_list = [] # Combination list
    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.with_entities(
            PROVIDER_SERVERS_MODEL_MAP[provider].region).distinct(
                PROVIDER_SERVERS_MODEL_MAP[provider].region)
    if hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region'):
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.with_entities(
            PROVIDER_IMAGES_MODEL_MAP[provider].region).distinct(
                PROVIDER_IMAGES_MODEL_MAP[provider].region)
    for server in servers:
        if server.region not in region_list:
            region_list.append(server.region)
    for image in images:
        if image.region not in region_list:
            region_list.append(image.region)
    return [{'name': r } for r in region_list]


def _get_all_azure_regions():
    regions = []
    environments = MicrosoftRegionMapModel.query.all()
    for environment in environments:
        if environment.region not in regions:
            regions.append(environment.region)
        if environment.canonicalname not in regions:
            regions.append(environment.canonicalname)
    return [{'name': r } for r in sorted(regions)]


def _get_azure_servers(region, server_type=None):
    # first lookup canonical name for the given region
    environment = MicrosoftRegionMapModel.query.filter(
        or_(MicrosoftRegionMapModel.region == region,
            MicrosoftRegionMapModel.canonicalname == region)).first()

    if not environment:
        abort(Response('', status=404))

    # then get all the regions with the canonical name
    environments = MicrosoftRegionMapModel.query.filter(
        MicrosoftRegionMapModel.canonicalname == environment.canonicalname)

    # get all the possible names for the region
    all_regions = []
    for environment in environments:
        if environment.region not in all_regions:
            all_regions.append(environment.region)

    # get all the severs for that region
    if server_type:
        servers = MicrosoftServersModel.query.filter(
            MicrosoftServersModel.type == server_type,
            MicrosoftServersModel.region.in_(all_regions))
    else:
        servers = MicrosoftServersModel.query.filter(
            MicrosoftServersModel.region.in_(all_regions))

    try:
        return [
            get_formatted_dict(server) for server in servers]
    except DataError:
        abort(Response('', status=404))


def _get_azure_images_for_region_state(region, state):
    # first lookup the environment for the given region
    environment = MicrosoftRegionMapModel.query.filter(
        or_(MicrosoftRegionMapModel.region == region,
            MicrosoftRegionMapModel.canonicalname == region)).first()

    if not environment:
        abort(Response('', status=404))

    # assume the environment is unique per region
    environment_name = environment.environment

    # now pull all the images that matches the environment and state
    if state is None:
        images = MicrosoftImagesModel.query.filter(
            MicrosoftImagesModel.environment == environment_name)
    else:
        images = MicrosoftImagesModel.query.filter(
            MicrosoftImagesModel.environment == environment_name,
            MicrosoftImagesModel.state == state)

    extra_attrs = {'region': region}
    try:
        return [get_formatted_dict(
            image, extra_attrs=extra_attrs) for image in images]
    except DataError:
        abort(Response('', status=404))


def get_provider_images_for_region_and_state(provider, region, state):
    images = []
    if provider == 'microsoft':
        return _get_azure_images_for_region_state(region, state)

    region_names = []
    for each in get_provider_regions(provider):
        region_names.append(each['name'])
    if state in ImageState.__members__ and region in region_names:
        if (hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region')):
            images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
                PROVIDER_IMAGES_MODEL_MAP[provider].region == region,
                PROVIDER_IMAGES_MODEL_MAP[provider].state == state)
        else:
            images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
                PROVIDER_IMAGES_MODEL_MAP[provider].state == state)

        return [get_formatted_dict(image) for image in images]
    else:
        abort(Response('', status=404))


def get_provider_images_for_state(provider, state):
    if state in ImageState.__members__:
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].state == state)
    else:
        abort(Response('', status=404))
    return [get_formatted_dict(image) for image in images]



def get_provider_servers_for_region(provider, region):
    servers = []
    if provider == 'microsoft':
        return _get_azure_servers(region)

    region_names = []
    for each in get_provider_regions(provider):
        region_names.append(each['name'])
    if region in region_names:
        if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
            servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
                PROVIDER_SERVERS_MODEL_MAP[provider].region == region)
    else:
        abort(Response('', status=404))

    return [get_formatted_dict(server) for server in servers]


def get_provider_servers_for_region_and_type(provider, region, server_type):
    servers = []
    if provider == 'microsoft':
        return _get_azure_servers(region, server_type)

    region_names = []
    for each in get_provider_regions(provider):
        region_names.append(each['name'])
    if (PROVIDER_SERVERS_MODEL_MAP.get(provider) != None and
            server_type in get_provider_servers_types(provider) and
            region in region_names):
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
            PROVIDER_SERVERS_MODEL_MAP[provider].region == region,
            PROVIDER_SERVERS_MODEL_MAP[provider].type == server_type)
        return [get_formatted_dict(server) for server in servers]
    else:
        abort(Response('', status=404))

def get_provider_images_for_region(provider, region):
    if provider == 'microsoft':
        return _get_azure_images_for_region_state(region, None)

    images = []
    region_names = []
    for each in get_provider_regions(provider):
        region_names.append(each['name'])
    if region in region_names:
        if hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region'):
            images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
                PROVIDER_IMAGES_MODEL_MAP[provider].region == region)
    else:
        abort(Response('', status=404))
    return [get_formatted_dict(image) for image in images]


def get_provider_servers(provider):
    servers = []
    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.all()
    return [get_formatted_dict(server) for server in servers]


def get_provider_images(provider):
    images = PROVIDER_IMAGES_MODEL_MAP[provider].query.all()
    return [get_formatted_dict(image) for image in images]


def get_data_version_for_provider_category(provider, category):
    tablename = provider + category
    try:
        version = VersionsModel.query.filter(
            VersionsModel.tablename == tablename).one()
    except (NoResultFound, MultipleResultsFound):
        # NOTE(gyee): we should never run into MultipleResultsFound exception
        # or otherse we have data corruption problem in the database.
        abort(Response('', status=404))

    return {'version': str(version.version)}


def assert_valid_provider(provider):
    provider = provider.lower()
    supported_providers = get_supported_providers()
    if provider not in supported_providers:
        abort(Response('', status=404))


def assert_valid_category(category):
    if category not in SUPPORTED_CATEGORIES:
        abort(Response('', status=400))


def make_response(content_dict, collection_name, element_name):
    if request.path.endswith('.xml'):
        return Response(
            json_to_xml(content_dict, collection_name, element_name),
            mimetype='application/xml;charset=utf-8')
    else:
        if collection_name:
            content = {collection_name: content_dict}
        else:
            content = content_dict
        return jsonify(**content)


@app.route('/v1/providers', methods=['GET'])
@app.route('/v1/providers.json', methods=['GET'])
@app.route('/v1/providers.xml', methods=['GET'])
def list_providers():
    providers = get_providers()
    return make_response(providers, 'providers', 'provider')


@app.route('/v1/<provider>/servers/types', methods=['GET'])
@app.route('/v1/<provider>/servers/types.json', methods=['GET'])
@app.route('/v1/<provider>/servers/types.xml', methods=['GET'])
def list_provider_servers_types(provider):
    assert_valid_provider(provider)
    servers_types = get_provider_servers_types(provider)
    return make_response(servers_types, 'types', 'type')


@app.route('/v1/images/states', methods=['GET'])
@app.route('/v1/images/states.json', methods=['GET'])
@app.route('/v1/images/states.xml', methods=['GET'])
def list_images_states():
    states = []
    for attr in dir(ImageState):
        if attr[0] == '_':
            continue
        else:
            states.append({'name': attr})
    return make_response(states, 'states', 'state')


@app.route('/v1/<provider>/regions', methods=['GET'])
@app.route('/v1/<provider>/regions.json', methods=['GET'])
@app.route('/v1/<provider>/regions.xml', methods=['GET'])
def list_provider_regions(provider):
    assert_valid_provider(provider)
    regions = get_provider_regions(provider)
    return make_response(regions, 'regions', 'region')


@app.route('/v1/<provider>/<region>/servers/<server_type>', methods=['GET'])
@app.route('/v1/<provider>/<region>/servers/<server_type>.json',
           methods=['GET'])
@app.route('/v1/<provider>/<region>/servers/<server_type>.xml',
           methods=['GET'])
def list_servers_for_provider_region_and_type(provider, region, server_type):
    assert_valid_provider(provider)
    servers = get_provider_servers_for_region_and_type(provider,
        region, server_type)
    return make_response(servers, 'servers', 'server')


@app.route('/v1/<provider>/servers/<server_type>', methods=['GET'])
@app.route('/v1/<provider>/servers/<server_type>.json', methods=['GET'])
@app.route('/v1/<provider>/servers/<server_type>.xml', methods=['GET'])
def list_servers_for_provider_type(provider, server_type):
    assert_valid_provider(provider)
    servers = get_provider_servers_for_type(provider, server_type)
    return make_response(servers, 'servers', 'server')


@app.route('/v1/<provider>/<region>/images/<state>', methods=['GET'])
@app.route('/v1/<provider>/<region>/images/<state>.json', methods=['GET'])
@app.route('/v1/<provider>/<region>/images/<state>.xml', methods=['GET'])
def list_images_for_provider_region_and_state(provider, region, state):
    assert_valid_provider(provider)
    images = get_provider_images_for_region_and_state(provider, region, state)
    return make_response(images, 'images', 'image')


@app.route('/v1/<provider>/images/<state>', methods=['GET'])
@app.route('/v1/<provider>/images/<state>.json', methods=['GET'])
@app.route('/v1/<provider>/images/<state>.xml', methods=['GET'])
def list_images_for_provider_state(provider, state):
    assert_valid_provider(provider)
    images = get_provider_images_for_state(provider, state)
    return make_response(images, 'images', 'image')


@app.route('/v1/<provider>/<region>/<category>', methods=['GET'])
@app.route('/v1/<provider>/<region>/<category>.json', methods=['GET'])
@app.route('/v1/<provider>/<region>/<category>.xml', methods=['GET'])
def list_provider_resource_for_category(provider, region, category):
    assert_valid_provider(provider)
    assert_valid_category(category)
    resources = globals()['get_provider_%s_for_region' % (category)](
        provider, region)
    return make_response(resources, category, category[:-1])


@app.route('/v1/<provider>/<category>', methods=['GET'])
@app.route('/v1/<provider>/<category>.json', methods=['GET'])
@app.route('/v1/<provider>/<category>.xml', methods=['GET'])
def list_provider_resource(provider, category):
    assert_valid_provider(provider)
    assert_valid_category(category)
    resources = globals()['get_provider_%s' % (category)](provider)
    return make_response(resources, category, category[:-1])


@app.route('/v1/<provider>/dataversion', methods=['GET'])
@app.route('/v1/<provider>/dataversion.json', methods=['GET'])
@app.route('/v1/<provider>/dataversion.xml', methods=['GET'])
def get_provider_category_data_version(provider):
    assert_valid_provider(provider)
    category = request.args.get('category')
    assert_valid_category(category)
    version = get_data_version_for_provider_category(provider, category)
    return make_response(version, None, None)


@app.route('/', methods=['GET'])
def redirect_to_public_cloud():
    #return redirect('https://www.suse.com/solutions/public-cloud/')
    headers = {
        'Location': 'https://www.suse.com/solutions/public-cloud/',
    }
    return Response('', status=301, headers=headers)


@app.route('/<path:path>')
def catch_all(path):
    abort(Response('', status=400))


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.run()
