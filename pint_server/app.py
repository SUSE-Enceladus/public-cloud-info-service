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
import math
import re
from decimal import Decimal
from flask import (
    abort,
    Flask,
    jsonify,
    make_response,
    redirect,
    request,
    Response)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    desc,
    or_,
    text)
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from xml.dom import minidom
import xml.etree.ElementTree as ET

import pint_server
from pint_server.database import init_db, get_psql_server_version
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
    'regionserver-sap': 'region',
    'regionserver-sles': 'region',
    'update': 'update',
    'region': 'region'
}

REGIONSERVER_SMT_REVERSED_MAP = {
    'update': 'smt',
    'region': 'regionserver'
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

PROVIDER_IMAGES_EXCLUDE_ATTRS = {
    'microsoft': ['id']
}

PROVIDER_SERVERS_EXCLUDE_ATTRS = {
    'amazon': ['id'],
    'google': ['id'],
    'microsoft': ['id']
}

SUPPORTED_CATEGORIES = ['images', 'servers']

# NOTE: AWS lambda payload size cannot exceed 6MB. We are setting the
# maximum payload size to 5.5MB to account for the HTTP protocol overheads
MAX_PAYLOAD_SIZE = 5500000


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
        # FIXME(gyee): the orignal Pint server does not return the "changeinfo"
        # or "urn" attribute if it's empty. So we'll need to do the same here.
        # IMHO, I consider that a bug in the original Pint server as we should
        # return all attributes regardless whether its empty or not.
        if attr.lower() in ['urn', 'changeinfo'] and not obj.__dict__[attr]:
            continue

        # NOTE: the "shape" attribute will be processed together with "type"
        # as it is internal only
        if attr.lower() == 'shape':
            continue

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
                # NOTE(gyee): we need to reverse map the server type
                # to make it backward compatible
                if obj.__dict__['shape']:
                    obj_dict[attr] = "%s-%s" % (
                        REGIONSERVER_SMT_REVERSED_MAP[obj.type.value],
                        obj.__dict__['shape'])
                else:
                     obj_dict[attr] = (
                         REGIONSERVER_SMT_REVERSED_MAP[obj.type.value])
            elif isinstance(value, datetime.date):
                obj_dict[attr] = value.strftime('%Y%m%d')
            else:
                obj_dict[attr] = null_to_empty(value)
    if extra_attrs:
        obj_dict.update(extra_attrs)
    return obj_dict


def get_mapped_server_type_for_provider(provider, server_type):
    if server_type not in REGIONSERVER_SMT_MAP:
        abort(Response('', status=404))
    mapped_server_type = REGIONSERVER_SMT_MAP[server_type]
    if PROVIDER_SERVERS_MODEL_MAP.get(provider):
        server_types_json = get_provider_servers_types(provider)
        server_types = [t['name'] for t in server_types_json]
        if mapped_server_type not in server_types:
            abort(Response('', status=404))
    return mapped_server_type


def get_provider_servers_for_type(provider, server_type):
    servers = []
    mapped_server_type = get_mapped_server_type_for_provider(
        provider, server_type)
    # NOTE(gyee): currently we don't have DB tables for both Alibaba and
    # Oracle servers. In order to maintain compatibility with the
    # existing Pint server, we are returning an empty list.
    if not PROVIDER_SERVERS_MODEL_MAP.get(provider):
        return servers

    servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
        PROVIDER_SERVERS_MODEL_MAP[provider].type == mapped_server_type)
    exclude_attrs = PROVIDER_SERVERS_EXCLUDE_ATTRS.get(provider)
    return [get_formatted_dict(server, exclude_attrs=exclude_attrs)
            for server in servers]


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
        mapped_server_type = get_mapped_server_type_for_provider(
            'microsoft', server_type)
        servers = MicrosoftServersModel.query.filter(
            MicrosoftServersModel.type == mapped_server_type,
            MicrosoftServersModel.region.in_(all_regions))
    else:
        servers = MicrosoftServersModel.query.filter(
            MicrosoftServersModel.region.in_(all_regions))

    try:
        exclude_attrs = PROVIDER_SERVERS_EXCLUDE_ATTRS.get('microsoft')
        return [get_formatted_dict(server, exclude_attrs=exclude_attrs)
                for server in servers]
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
    exclude_attrs = PROVIDER_IMAGES_EXCLUDE_ATTRS.get('microsoft')
    try:
        return [get_formatted_dict(image, extra_attrs=extra_attrs,
                                   exclude_attrs=exclude_attrs)
                for image in images]
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

        exclude_attrs = PROVIDER_IMAGES_EXCLUDE_ATTRS.get(provider)
        return [get_formatted_dict(image, exclude_attrs=exclude_attrs)
                for image in images]
    else:
        abort(Response('', status=404))


def get_provider_images_for_state(provider, state):
    if state in ImageState.__members__:
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].state == state)
    else:
        abort(Response('', status=404))
    exclude_attrs = PROVIDER_IMAGES_EXCLUDE_ATTRS.get(provider)
    return [get_formatted_dict(image, exclude_attrs=exclude_attrs)
            for image in images]



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

    exclude_attrs = PROVIDER_SERVERS_EXCLUDE_ATTRS.get(provider)
    return [get_formatted_dict(server, exclude_attrs=exclude_attrs)
            for server in servers]


def get_provider_servers_for_region_and_type(provider, region, server_type):
    if provider == 'microsoft':
        return _get_azure_servers(region, server_type)

    servers = []
    mapped_server_type = get_mapped_server_type_for_provider(
        provider, server_type)
    # NOTE(gyee): for Alibaba and Oracle where we don't have any servers,
    # we are returning an empty list to be backward compatible.
    if not PROVIDER_SERVERS_MODEL_MAP.get(provider):
        return servers

    region_names = []
    for each in get_provider_regions(provider):
        region_names.append(each['name'])
    if region in region_names:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
            PROVIDER_SERVERS_MODEL_MAP[provider].region == region,
            PROVIDER_SERVERS_MODEL_MAP[provider].type == mapped_server_type)
        exclude_attrs = PROVIDER_SERVERS_EXCLUDE_ATTRS.get(provider)
        return [get_formatted_dict(server, exclude_attrs=exclude_attrs)
                for server in servers]
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
    exclude_attrs = PROVIDER_IMAGES_EXCLUDE_ATTRS.get(provider)
    return [get_formatted_dict(image, exclude_attrs=exclude_attrs)
            for image in images]


def get_provider_servers(provider):
    servers = []
    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.all()
    exclude_attrs = PROVIDER_SERVERS_EXCLUDE_ATTRS.get(provider)
    return [get_formatted_dict(server, exclude_attrs=exclude_attrs)
            for server in servers]


def trim_images_payload(images):
    payload_size = jsonify(images=images).content_length

    if payload_size >  MAX_PAYLOAD_SIZE:
        # NOTE: assuming the size of the entries are evenly distributed, we
        # determine the percentage of entries to trim from the end of the list,
        # as the list is sorted in decending order by publishedon date, by
        # calculating the percentage over the maximum payload size. Then
        # trim the same percentage off the list, rounding up to be safe.
        trim_size  = math.ceil(
            ((payload_size - MAX_PAYLOAD_SIZE) / payload_size) * len(images))
        last_publishedon = images[-trim_size]['publishedon']
        images = images[:-trim_size]

        # Now make sure we don't have partial data by finished triming all the
        # images from all regions that have the same publishedon date that of
        # the last image that got trimmed.
        trim_size = 0
        while images[-(trim_size + 1)]['publishedon'] == last_publishedon:
            trim_size += 1
        if trim_size:
            images = images[:-trim_size]
    return images


def get_provider_images(provider):
    images = PROVIDER_IMAGES_MODEL_MAP[provider].query.order_by(
        desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()
    exclude_attrs = PROVIDER_IMAGES_EXCLUDE_ATTRS.get(provider)
    return trim_images_payload(
            [get_formatted_dict(image, exclude_attrs=exclude_attrs)
                for image in images])


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


@app.route('/package-version', methods=['GET'])
def get_package_version():
    return make_response(
        {'package version': pint_server.__VERSION__}, None, None)


@app.route('/db-server-version', methods=['GET'])
def get_db_server_version():
    db_version = get_psql_server_version(db_session)
    return make_response(
        {'database server version': db_version}, None, None)
    

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
