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
import os
import re
import gzip
import bz2
import lzma
import json 
from collections import namedtuple
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from flask import (
    abort,
    Flask,
    jsonify,
    redirect,
    request,
    Response)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    desc,
    asc,
    or_,
    text)
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from xml.dom import minidom
import xml.etree.ElementTree as ET

import pint_server
from pint_models.database import init_db, get_psql_server_version
from pint_models.models import (ImageState, AmazonImagesModel,
                                OracleImagesModel, AlibabaImagesModel,
                                MicrosoftImagesModel, GoogleImagesModel,
                                AmazonServersModel, MicrosoftServersModel,
                                GoogleServersModel, ServerType,
                                VersionsModel, MicrosoftRegionMapModel)


# hashable helper class to create named tuples from the details in
# an image entry that are relevant for deletion date tracking.
DeletionDetails = namedtuple("DeletionDetails",
                             " ".join(["state",
                                       "deprecatedon",
                                       "deletedon"]))


# helper regexp matcher for dates specified in the %Y%m%d (4 digits
# for year, 2 digits for month, 2 digits for day) format
date_matcher = re.compile(
    r'\d{4}' +  # 4 digit year
    r'(' +  # 2 digit month, 2 digit day
    # Months with 31 days
    r'(01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])' +
    r'|' +
    # Months with 30 days
    r'(04|06|09|11)(0[1-9]|[1-2][0-9]|30)' +
    r'|' +
    # February
    r'02(0[1-9]|[1-2][0-9])' +
    r')' +
    r''
)


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
# default maximum payload size to 5.0MB to account for the HTTP protocol
# overheads. However, this value can be overwritten with the
# "MAX_PAYLOAD_SIZE" environment variable.
DEFAULT_MAX_PAYLOAD_SIZE = 5000000

# Provider specific deletion relative time deltas
DELETION_RELATIVE_DELTA_MAP = {
    'amazon': {
        'years':2,
        'months':0,
        'days':0
    }
}

# Default deletion relative time deltas
DELETION_RELATIVE_DELTA_DEFAULT = {
    'years':0,
    'months':6,
    'days':0
}


DATE_FORMAT = '%Y%m%d'


def get_deletion_relative_delta(provider):
    return relativedelta(**DELETION_RELATIVE_DELTA_MAP.get(
            provider, DELETION_RELATIVE_DELTA_DEFAULT))


def get_datetime_date(date):
    try:
        return datetime.datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        abort(Response('', status=404))


def get_supported_providers():
    versions  = VersionsModel.query.with_entities(VersionsModel.tablename)
    # sort the list of providers so that the order is consistent going forward
    return sorted({re.sub('(servers|images)', '', v.tablename) for v in versions})


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
    # make exclude attrs an empty list if not specified so that we
    # don't have to check for it being non-None on every iteration
    # below
    if exclude_attrs is None:
        exclude_attrs = []

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

        if attr in exclude_attrs:
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
                obj_dict[attr] = value.strftime(DATE_FORMAT)
            else:
                obj_dict[attr] = null_to_empty(value)
    if extra_attrs:
        obj_dict.update(extra_attrs)
    return obj_dict


# Helper functions for performing provider specific formatting of
# the response dictionary
def formatted_provider_results(provider, results, exclude_attrs, extra_attrs):

    try:
        formatted = [get_formatted_dict(r,
                                        exclude_attrs=exclude_attrs,
                                        extra_attrs=extra_attrs)
                     for r in results]
    except DataError:
        abort(Response('', status=404))

    return formatted


# Formatting helper for provider image list results
def formatted_provider_images(provider, images, extra_attrs=None):
    # retrieve list of attrs that should be excluded for provider images
    exclude_attrs = PROVIDER_IMAGES_EXCLUDE_ATTRS.get(provider)

    return formatted_provider_results(provider, images,
                                      exclude_attrs=exclude_attrs,
                                      extra_attrs=extra_attrs)


# Formatting helper for provider image list results
def formatted_provider_servers(provider, servers, extra_attrs=None):
    # retrieve list of attrs that should be excluded for provider servers
    exclude_attrs = PROVIDER_SERVERS_EXCLUDE_ATTRS.get(provider)

    return formatted_provider_results(provider, servers,
                                      exclude_attrs=exclude_attrs,
                                      extra_attrs=extra_attrs)


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
    return formatted_provider_servers(provider, servers)


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


def query_provider_regions(provider):
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

    return region_list


def get_provider_regions(provider):

    regions = query_provider_regions(provider)

    return [{'name': r } for r in regions]


def _get_all_azure_regions():
    regions = set()
    environments = MicrosoftRegionMapModel.query.all()
    for environment in environments:
        regions.update((environment.region, environment.canonicalname))
    return sorted(regions)


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

    return formatted_provider_servers('microsoft', servers)


def _get_azure_environment_name_for_region(region):
    # lookup environment for given region, assuming unique per region
    environment = MicrosoftRegionMapModel.query.filter(
        or_(MicrosoftRegionMapModel.region == region,
            MicrosoftRegionMapModel.canonicalname == region)).first()

    if not environment:
        abort(Response('', status=404))

    return environment.environment

def _get_azure_images_for_region_state(provider, region, state=None):
    environment_name = _get_azure_environment_name_for_region(region)

    # query all images with matching environment and state (if specified)
    if state is None:
        images = MicrosoftImagesModel.query.filter(
            MicrosoftImagesModel.environment == environment_name).order_by(
            desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()
    else:
        images = MicrosoftImagesModel.query.filter(
            MicrosoftImagesModel.environment == environment_name,
            MicrosoftImagesModel.state == state).order_by(
            desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()

    return images


def query_provider_images_for_region_and_state(provider, region, state):

    if provider == 'microsoft':
        images = _get_azure_images_for_region_state(provider, region, state)

    elif (hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region')):
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].region == region,
            PROVIDER_IMAGES_MODEL_MAP[provider].state == state).order_by(
            desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()
    else:
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].state == state).order_by(
            desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()

    return images


def get_provider_images_for_region_and_state(provider, region, state):
    images = query_provider_images_for_region_and_state(
            provider, region, state)

    extra_attrs = {}
    if provider == 'microsoft':
        extra_attrs['region'] = region

    return formatted_provider_images(provider, images, extra_attrs)


def get_provider_images_for_state(provider, state):
    images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
        PROVIDER_IMAGES_MODEL_MAP[provider].state == state).order_by(
        desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()
    return trim_images_payload(
                formatted_provider_images(provider, images))


def _get_azure_deprecatedby_images_for_region(provider, deprecatedby, region):
    environment_name = _get_azure_environment_name_for_region(region)

    # query all images with matching environment, in the deprecated
    # state, with a deprecatedon date <= deprecatedby.
    images = MicrosoftImagesModel.query.filter(
        MicrosoftImagesModel.environment == environment_name,
        MicrosoftImagesModel.state == ImageState.deprecated,
        MicrosoftImagesModel.deprecatedon < deprecatedby,
    ).order_by(desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()


    return images


def query_deletedby_images_in_provider_region(
        deletedby, provider, region=None
    ):

    # get provider specific relative delta for deletions
    deletion_delta = get_deletion_relative_delta(provider)

    # calculate deprecatedby data associated with deletedby date
    deprecatedby = deletedby - deletion_delta

    images = None

    if region:
        # microsoft needs special handling for region queries
        if provider == 'microsoft':
            images = _get_azure_deprecatedby_images_for_region(provider,
                                                               deprecatedby,
                                                               region)
        # if provider images table has region column retrieve matching images
        elif hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region'):
            images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
                PROVIDER_IMAGES_MODEL_MAP[provider].region == region,
                PROVIDER_IMAGES_MODEL_MAP[provider].state == ImageState.deprecated,
                PROVIDER_IMAGES_MODEL_MAP[provider].deprecatedon < deprecatedby,
            ).order_by(asc(PROVIDER_IMAGES_MODEL_MAP[provider].deletedon)).all()

    # if region was not specified, or provider wasn't microsoft or
    # provider images table doesn't have a region column
    if images is None:
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].state == ImageState.deprecated,
            PROVIDER_IMAGES_MODEL_MAP[provider].deprecatedon < deprecatedby,
        ).order_by(desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()

    return images


def get_provider_images_to_be_deletedby(deletedby, provider, region=None):
    images = query_deletedby_images_in_provider_region(
        deletedby, provider, region)

    extra_attrs = {}
    if region and provider == 'microsoft':
        extra_attrs['region'] = region

    return formatted_provider_images(provider, images,
                                     extra_attrs=extra_attrs)


def _query_image_in_azure_region(image_name, provider, region):
    # lookup environment for given region, assuming unique per region
    environment_name = _get_azure_environment_name_for_region(region)

    # retrieve matching images for region
    images = MicrosoftImagesModel.query.filter(
        MicrosoftImagesModel.environment == environment_name,
        MicrosoftImagesModel.name == image_name).order_by(
        desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()

    return images


def query_image_in_provider_region(image_name, provider, region=None):
    images = None

    if region:
        # microsoft needs special handling for region queries
        if provider == 'microsoft':
            images = _query_image_in_azure_region(image_name, provider, region)
        # if provider images table has region column retrieve matching images
        elif (hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region')):
            images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
                PROVIDER_IMAGES_MODEL_MAP[provider].region == region,
                PROVIDER_IMAGES_MODEL_MAP[provider].name == image_name).order_by(
                desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()

    # if region was not specified, or provider wasn't microsoft or
    # provider images table doesn't have region column
    if images is None:
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].name == image_name).order_by(
            desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()


    return images


def get_image_deletiondate_in_provider(image, provider, region=None):

    images = query_image_in_provider_region(image, provider, region)

    # if no images were found then the provided image name is invalid
    if len(images) == 0:
        abort(Response('', status=404))

    # depending on provider there may be multiple images all of
    # which should have the same state, deprecatedon and deletedon
    # values. Use a set to eliminate duplicates, and a namedtuple
    # helper to create a hashable object.
    image_set = {DeletionDetails(i.state,
                                 i.deprecatedon,
                                 i.deletedon)
                 for i in images
                 if i.state in [ImageState.deprecated,
                                ImageState.deleted]}

    # If we get back multiple sets of results, we should use
    # the earliest deprecatedon or deletedon date depending on
    # the found state(s).
    if len(image_set) > 1:
        image_states = {i.state for i in image_set}
        deprecatedon_dates = sorted({i.deprecatedon for i in image_set if i.deprecatedon})
        if not deprecatedon_dates:
            deprecatedon_dates = ['']
        deletedon_dates = sorted({i.deletedon for i in image_set if i.deletedon})
        if not deletedon_dates:
            deletedon_dates = ['']

        if ImageState.deleted in image_states:
            image_state = ImageState.deleted
        else:
            image_state = ImageState.deprecated

        image_set = set([DeletionDetails(image_state,
                                         deprecatedon_dates[0],
                                         deletedon_dates[0])])

    # if image is in not in deprecated/deleted state the image set
    # will be empty, so the result will be an empty deletiondate.
    if len(image_set) < 1:
        result = ""

    else:
        image = image_set.pop()

        # if the image is already in the deleted state return the
        # deletedon date.
        if image.state == ImageState.deleted:
            deletiondate = image.deletedon
        else:
            # otherwise calculate the expected deletion date using the
            # provider specific relative deletion delta
            deletiondate = image.deprecatedon + get_deletion_relative_delta(
                                                    provider)

        # result is determined deltion date
        result = deletiondate.strftime(DATE_FORMAT)

    return dict(deletiondate=result)


def get_provider_servers_for_region(provider, region):
    servers = []
    if provider == 'microsoft':
        return _get_azure_servers(region)

    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
            PROVIDER_SERVERS_MODEL_MAP[provider].region == region)

    return formatted_provider_servers(provider, servers)


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

    servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.filter(
        PROVIDER_SERVERS_MODEL_MAP[provider].region == region,
        PROVIDER_SERVERS_MODEL_MAP[provider].type == mapped_server_type)
    return formatted_provider_servers(provider, servers)

def get_provider_images_for_region(provider, region):
    images = []
    extra_attrs = {}
    if provider == 'microsoft':
        images = _get_azure_images_for_region_state(provider, region, None)
        extra_attrs['region'] = region

    elif hasattr(PROVIDER_IMAGES_MODEL_MAP[provider], 'region'):
        images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].region == region).order_by(
            desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()
    return formatted_provider_images(provider, images, extra_attrs)


def get_provider_servers(provider):
    servers = []
    if PROVIDER_SERVERS_MODEL_MAP.get(provider) != None:
        servers = PROVIDER_SERVERS_MODEL_MAP[provider].query.all()
    return formatted_provider_servers(provider, servers)

def get_max_payload_size():
    if 'MAX_PAYLOAD_SIZE' in os.environ:
        return int(os.environ.get('MAX_PAYLOAD_SIZE'))
    else:
        return DEFAULT_MAX_PAYLOAD_SIZE


def trim_images_payload(images):
    payload_size = jsonify(images=images).content_length
    max_payload_size = get_max_payload_size()
    accepted_encodings = acceptable_encodings()
    if not supported_encoding(accepted_encodings) and (payload_size > max_payload_size):
        images = get_trimmed_images(payload_size, max_payload_size, images)
    return images


def get_trimmed_images(payload_size, max_payload_size, images):
    # NOTE: assuming the size of the entries are evenly distributed, we
    # determine the percentage of entries to trim from the end of the list,
    # as the list is sorted in decending order by publishedon date, by
    # calculating the percentage over the maximum payload size. Then
    # trim the same percentage off the list, rounding up to be safe.
    trim_size  = math.ceil(
        ((payload_size - max_payload_size) / payload_size) * len(images))
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
    images = PROVIDER_IMAGES_MODEL_MAP[provider].query.filter(
            PROVIDER_IMAGES_MODEL_MAP[provider].state.in_([
                ImageState.active,
                ImageState.inactive,
                ImageState.deprecated])).order_by(
        desc(PROVIDER_IMAGES_MODEL_MAP[provider].publishedon)).all()
    return trim_images_payload(
                formatted_provider_images(provider, images))


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


def assert_valid_provider_region(provider, region):
    provider_regions = query_provider_regions(provider)
    if region not in provider_regions:
        abort(Response('', status=404))


def assert_valid_state(state):
    if state not in ImageState.__members__:
        abort(Response('', status=404))


def assert_valid_category(category):
    if category not in SUPPORTED_CATEGORIES:
        abort(Response('', status=400))


def assert_valid_date(date):
    if not date_matcher.match(date):
        abort(Response('', status=404))


def acceptable_encodings():
    accept_encoding = request.headers.get("Accept-Encoding")
    if not accept_encoding:
        return []
    return [e.strip() for e in accept_encoding.split(",")]


def supported_encoding(accept_encoding):
    return (accept_encoding is not None) and any(comp_type in accept_encoding for comp_type in (
            'bzip2', 'gzip', 'xz'))


def make_response_payload(
        content_dict, collection_name, element_name, charset):
    # generate xml or json formatted payload
    if 'xml' in request.path:
        payload = json_to_xml(content_dict, collection_name, element_name)
        app_type = 'xml'
    else:
        if collection_name:
            content = {collection_name: content_dict}
        else:
            content = content_dict
        payload = json.dumps(content, separators=(',', ':'))
        app_type = 'json'

    # encode the payload with the desired charset
    payload = payload.encode(charset)
    return app_type, payload


def make_response(content_dict, collection_name, element_name):

    charset = 'utf-8'
    content_encoding_header = None
    app_type, payload = make_response_payload(
        content_dict, collection_name, element_name, charset)
    content_type = 'application/%s;charset=%s' % (app_type, charset)

    accepted_encodings = acceptable_encodings()
    if supported_encoding(accepted_encodings):
        if 'bzip2' in accepted_encodings:
            compression_type = 'bz2'
            content_encoding_header = 'bzip2'
        elif 'gzip' in accepted_encodings:
            compression_type = 'gzip'
            content_encoding_header = 'gzip'
        elif 'xz' in accepted_encodings:
            compression_type = 'lzma'
            content_encoding_header = 'lzma'

        app_type, payload = make_compressed_response(
            payload, collection_name, element_name, compression_type)

    mimetype = 'application/%s;charset=%s' % (app_type, charset)
    response = Response(payload, mimetype=mimetype)
    if content_encoding_header:
        response.headers["Content-Encoding"] = content_encoding_header
        response.headers["Content-Type"] = content_type
    return response


def make_compressed_response(
        payload, collection_name, element_name, compression_type):
     uncompressed_payload = payload
     payload = get_compressed_payload(payload, compression_type)
     max_payload_size = get_max_payload_size()

     # Check length of compressed payload
     if len(payload) > max_payload_size:
         max_size = get_max_payload_for_limit(
             uncompressed_payload, max_payload_size)

         # Trim the payload so that compressed data does not exceed
         # MAX_PAYLOAD_SIZE limit
         trimmed_payload = get_trimmed_images(
             len(uncompressed_payload), max_size, content_dict)

         app_type, temp_payload = make_response_payload(
             trimmed_payload, collection_name, element_name, charset)
         payload = get_compressed_payload(temp_payload, compression_type)

     app_type = compression_type
     return app_type, payload


def get_compressed_payload(payload, compression_type):
    if compression_type == "bz2":
        payload = bz2.compress(payload, compresslevel=9)
    elif compression_type == "gzip":
        payload = gzip.compress(payload, compresslevel=9)
    elif compression_type == "lzma":    
        payload = lzma.compress(payload, preset=9)

    return payload


# Estimates how much payload data can fit under MAX_PAYLOAD_SIZE compressed limit
def get_max_payload_for_limit(payload, limit_bytes):
    low, high = 0, len(payload)
    while low < high:
        mid = (low + high) // 2
        compressed = get_compressed_payload(payload[:mid], compression_type)
        if len(compressed) <= limit_bytes:
            low = mid + 1
        else:
            high = mid
    truncated = payload[:low-1]
    return len(truncated)


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
    assert_valid_provider_region(provider, region)
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
    assert_valid_provider_region(provider, region)
    assert_valid_state(state)
    images = get_provider_images_for_region_and_state(provider, region, state)
    return make_response(images, 'images', 'image')


@app.route('/v1/<provider>/<region>/images/deletiondate/<image>', methods=['GET'])
@app.route('/v1/<provider>/<region>/images/deletiondate/<image>.json', methods=['GET'])
@app.route('/v1/<provider>/<region>/images/deletiondate/<image>.xml', methods=['GET'])
def get_image_deletiondate_for_provider_region(provider, region, image):
    assert_valid_provider(provider)
    assert_valid_provider_region(provider, region)
    deletiondate = get_image_deletiondate_in_provider(image, provider, region)
    return make_response(deletiondate, None, None)


@app.route('/v1/<provider>/images/deletiondate/<image>', methods=['GET'])
@app.route('/v1/<provider>/images/deletiondate/<image>.json', methods=['GET'])
@app.route('/v1/<provider>/images/deletiondate/<image>.xml', methods=['GET'])
def get_image_deletiondate_for_provider(provider, image):
    assert_valid_provider(provider)
    deletiondate = get_image_deletiondate_in_provider(image, provider)
    return make_response(deletiondate, None, None)


@app.route('/v1/<provider>/<region>/images/deletedby/<date>', methods=['GET'])
@app.route('/v1/<provider>/<region>/images/deletedby/<date>.json', methods=['GET'])
@app.route('/v1/<provider>/<region>/images/deletedby/<date>.xml', methods=['GET'])
def list_images_deletedby_for_provider_region(provider, region, date):
    assert_valid_provider(provider)
    assert_valid_provider_region(provider, region)
    assert_valid_date(date)
    deletedby = get_datetime_date(date)
    images = get_provider_images_to_be_deletedby(deletedby, provider, region)
    return make_response(images, 'images', 'image')


@app.route('/v1/<provider>/images/deletedby/<date>', methods=['GET'])
@app.route('/v1/<provider>/images/deletedby/<date>.json', methods=['GET'])
@app.route('/v1/<provider>/images/deletedby/<date>.xml', methods=['GET'])
def list_images_deletedby_for_provider(provider, date):
    assert_valid_provider(provider)
    assert_valid_date(date)
    deletedby = get_datetime_date(date)
    images = get_provider_images_to_be_deletedby(deletedby, provider)
    return make_response(images, 'images', 'image')


# TODO(rtamalin):
#   Re-enable global deletedby request once make_response has been
#   updated to generate validly formated XML responses.
#@app.route('/v1/images/deletedby/<date>', methods=['GET'])
#@app.route('/v1/images/deletedby/<date>.json', methods=['GET'])
#@app.route('/v1/images/deletedby/<date>.xml', methods=['GET'])
#def list_images_deletedby(date):
#    assert_valid_date(date)
#    deletedby = get_datetime_date(date)
#    provider_images = {}
#    providers = []
#    for provider in PROVIDER_IMAGES_MODEL_MAP.keys():
#        providers.append(dict(name=provider,
#            images=get_provider_images_to_be_deletedby(deletedby,
#                                                       provider)))
#    return make_response(providers, 'providers', 'provider')


@app.route('/v1/<provider>/images/<state>', methods=['GET'])
@app.route('/v1/<provider>/images/<state>.json', methods=['GET'])
@app.route('/v1/<provider>/images/<state>.xml', methods=['GET'])
def list_images_for_provider_state(provider, state):
    assert_valid_provider(provider)
    assert_valid_state(state)
    images = get_provider_images_for_state(provider, state)
    return make_response(images, 'images', 'image')


@app.route('/v1/<provider>/<region>/<category>', methods=['GET'])
@app.route('/v1/<provider>/<region>/<category>.json', methods=['GET'])
@app.route('/v1/<provider>/<region>/<category>.xml', methods=['GET'])
def list_provider_resource_for_category(provider, region, category):
    assert_valid_provider(provider)
    assert_valid_provider_region(provider, region)
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
