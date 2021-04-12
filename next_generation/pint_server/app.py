import datetime
from decimal import Decimal
from flask import abort, Flask, jsonify, make_response, request, redirect, \
                  Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, or_
from xml.dom import minidom
import xml.etree.ElementTree as ET

from pint_server.database import engine, init_db, db_session
from pint_server.models import ImageState, AmazonImagesModel, \
                               OracleImagesModel, \
                               AlibabaImagesModel, MicrosoftImagesModel, \
                               GoogleImagesModel, AmazonServersModel, \
                               MicrosoftServersModel, GoogleServersModel, \
                               ServerType, VersionsModel, \
                               MicrosoftRegionMapModel


app = Flask(__name__)
init_db()

cors_config = {
    "origins": ["*"]
}
CORS(app, resources={
    r"/*": cors_config
})

# we don't care about modifications as we are doing DB read only
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


null_to_empty = lambda s : s or ''

CACHE_PROVIDERS = None

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
    global CACHE_PROVIDERS

    if CACHE_PROVIDERS is None:
        CACHE_PROVIDERS = query_providers()

    return CACHE_PROVIDERS


def query_providers():
    """Get all the providers"""
    global CACHE_PROVIDERS

    if CACHE_PROVIDERS is not None:
        return CACHE_PROVIDERS

    # FIXME(gyee): this query is very specific to PostgreSQL. If we support
    # other DBs such as MySQL, we'll need to conditionally change this.
    # Ideally, this information should be in a SQL lookup table so it's
    # database type agnostic.
    sql_stat = text("select regexp_replace(table_name, 'servers|images', '') "
                    "from information_schema.tables where "
                    "table_schema = 'public' and table_name like '%images'")
    result = engine.execute(sql_stat)
    CACHE_PROVIDERS = [row[0] for row in result]
    return CACHE_PROVIDERS


def get_providers():
    providers = query_providers()
    return [{'name': provider} for provider in providers]


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
    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
            PROVIDER_SERVERS_MODEL_MAP[provider].type == server_type)
    return [get_formatted_dict(server) for server in servers]


def get_provider_servers_types(provider):
    servers = []
    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.distinct(
            PROVIDER_SERVERS_MODEL_MAP[provider].type)
    return [{'name': server.type.value} for server in servers]


def get_provider_regions(provider):
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


def _get_azure_servers(region, server_type=None):
    # first lookup canonical name for the given region
    environments = MicrosoftRegionMapModel.query.filter(
        or_(MicrosoftRegionMapModel.region == region,
            MicrosoftRegionMapModel.canonicalname == region))

    # then get all the regions with the canonical name
    environments = MicrosoftRegionMapModel.query.filter(
        MicrosoftRegionMapModel.canonicalname == environments[0].canonicalname)

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
    return [
        get_formatted_dict(server) for server in servers]


def _get_azure_images_for_region_state(region, state):
    # first lookup the environment for the given region
    environments = MicrosoftRegionMapModel.query.filter(
        or_(MicrosoftRegionMapModel.region == region,
            MicrosoftRegionMapModel.canonicalname == region))

    # assume the environment is unique per region
    environment_name = environments[0].environment

    # now pull all the images that matches the environment and state
    images = MicrosoftImagesModel.query.filter(
        MicrosoftImagesModel.environment == environment_name,
        MicrosoftImagesModel.state == state)

    extra_attrs = {'region': region}
    return [
        get_formatted_dict(image, extra_attrs=extra_attrs) for image in images]


def get_provider_images_for_region_and_state(provider, region, state):
    images = []
    if provider == 'microsoft':
        return _get_azure_images_for_region_state(region, state)

    if hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region') \
            and hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'state'):
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].region == region,
            PROVIDER_IMAGES_MODEL_MAP[provider].state == state)
    return [get_formatted_dict(image) for image in images]


def get_provider_images_for_state(provider, state):
    images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
        PROVIDER_IMAGES_MODEL_MAP[provider].state == state)
    return [get_formatted_dict(image) for image in images]


def get_provider_servers_for_region(provider, region):
    servers = []
    if provider == 'microsoft':
        return _get_azure_servers(region)

    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
            PROVIDER_SERVERS_MODEL_MAP[provider].region == region)
    return [get_formatted_dict(server) for server in servers]


def get_provider_servers_for_region_and_type(provider, region, server_type):
    servers = []
    if provider == 'microsoft':
        return _get_azure_servers(region, server_type)

    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
            PROVIDER_SERVERS_MODEL_MAP[provider].region == region,
            PROVIDER_SERVERS_MODEL_MAP[provider].type == server_type)
    return [get_formatted_dict(server) for server in servers]


def get_provider_images_for_region(provider, region):
    images = []
    if hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region'):
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].region == region)
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
    column_name = provider + category
    versions = VersionsModel.query.all()[0]
    return {'version': str(float(getattr(versions, column_name)))}


def assert_valid_provider(provider):
    provider = provider.lower()
    supported_providers = get_supported_providers()
    if provider not in supported_providers:
        abort(Response('', status=404))


def assert_valid_category(category):
    if category not in SUPPORTED_CATEGORIES:
        abort(Response('', status=404))


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
