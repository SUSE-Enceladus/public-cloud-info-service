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

from datetime import datetime
from lxml import etree
from urllib.parse import quote_plus
import argparse
import click
import glob
import logging
import os
import re
import subprocess
import sys

from pint_server.database import init_db
from pint_server.models import (
            AlibabaImagesModel,
            AmazonImagesModel,
            AmazonServersModel,
            GoogleImagesModel,
            GoogleServersModel,
            ImageState,
            MicrosoftImagesModel,
            MicrosoftRegionMapModel,
            MicrosoftServersModel,
            OracleImagesModel,
            ServerType,
            VersionsModel
        )

class DataUpdateError(Exception):
    pass

class InvalidServerTypeErrror(DataUpdateError):
    pass

class MissingRequiredTablesErrror(DataUpdateError):
    pass

LOG = logging.getLogger(__name__)

def gen_data_files_list(pint_data_repo=None):

    if pint_data_repo is None:
        pint_data_repo = os.path.realpath(
                             os.path.join(
                                 os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", "pint-data"))

    LOG.debug("Pint Data repo: %s", repr(pint_data_repo))
    if not os.path.isdir(pint_data_repo):
        raise Exception('ERROR: pint-data repo directory %s not found')

    data_files_pattern = os.path.join(pint_data_repo, 'data', '*.xml')
    LOG.debug("Data Files pattern: %s", repr(data_files_pattern))

    data_files = glob.glob(data_files_pattern)
    LOG.debug("Data Files: %s", repr(data_files))

    return data_files


def get_commit_date(data_file):
    data_dir = os.path.dirname(data_file)

    output = subprocess.run(["bash", "-c",
                             "cd %s; git log -n1 --pretty='format:%s' "
                             "--date='format:%s' %s" %
                             (os.path.dirname(data_file), '%cd', '%Y%m%d',
                              os.path.basename(data_file))],
                             stdout=subprocess.PIPE)

    return output.stdout.decode('utf-8')


def extract_provider_data_rows(parent_node, child_name):
    rows = []

    server_type_matcher = re.compile('^(?:smt|regionserver)(?:-([A-Za-z]+))?$')
    for child_node in parent_node.findall(child_name):
        row = {}
        for attr, value in child_node.items():
            if not value:
                # NOTE: setting it to None seem to be compatible with any data
                # type
                attr_value = None
            elif attr == 'type':
                if 'smt' in value:
                    attr_value = ServerType.update
                else:
                    attr_value = ServerType.region
                # NOTE: make sure we also populate the 'shape' column if
                # 'smt' or 'regionserver' has '-sles' or '-sap' postfix.
                m = server_type_matcher.match(value)
                if m and m.group(1):
                    row['shape'] = m.group(1)
                else:
                    row['shape'] = ''
            elif attr == 'state':
                attr_value = getattr(ImageState, value)
            elif attr in ['deletedon', 'deprecatedon', 'publishedon']:
                attr_value = datetime.strptime(value, "%Y%m%d").date()
            else:
                attr_value = value
            row[attr] = attr_value
        rows.append(row)

    return rows


def extract_provider_region_map_rows(parent_node):
    rows = []

    for environment in parent_node.findall('environment'):
        env_name = environment.get('name')
        for region in environment.findall('region'):
            region_name = region.get('name')
            row = dict(environment=env_name,
                       region=region_name,
                       canonicalname=region_name)
            rows.append(row)
            for alternate in region.findall('alternate'):
                row = dict(environment=env_name,
                           region=alternate.get('name'),
                           canonicalname=region_name)
                rows.append(row)
        #con.commit()
    return rows


def extract_data_from_file(data_file, data_store):

    commit_date = get_commit_date(data_file)
    reg_map = None

    provider = os.path.basename(data_file).split('.')[0]
    # This version is just a "suggested" version that is
    # derived from the date stamp; the actual version that
    # will be set will depend on whether this suggested
    # value is greater than the existing version, in which
    # case it will be used. Otherwise the existing version
    # will be incremented to indicate an incremental update
    # of the table for the same date.
    data_store[provider] = dict(version=f"{commit_date}.0",
                                tables={})

    LOG.info("Extracting XML data for %s provider...", repr(provider))

    with open(data_file) as dfp:
        df_lines = dfp.readlines()
        provider_tables = {}

        # Strip any <xml> declaration from the start of file content to
        # appease the XML parser if an encoding has been specified.
        content = ''.join(df_lines[1:])
        root = etree.fromstring(content)

        for table_type in ['image', 'server']:
            table_name = table_type + "s"
            rows = extract_provider_data_rows(
                        root.findall(table_name)[0], table_type)

            # verify all server table rows have a valid type
            if table_type == 'server':
                for row in rows:
                    if not isinstance(row['type'], ServerType):
                        raise InvalidServerTypeError(
                            "Invalid ServerType: '%s' in "
                            "servers data for '%s'" %
                            (row['type'], provider))

            provider_tables[table_name] = rows

        if provider == 'microsoft':
            rows = extract_provider_region_map_rows(
                        root.findall('environments')[0])
            provider_tables['regionmap'] = rows

        data_store[provider]['tables'] = provider_tables

# Per-table overrides to used for existing entry checks
IDENTITY_OVERRIDES = {
    # For the microsoftimages use the column names associated with the
    # first unique constraint as the identity override column list.
    MicrosoftImagesModel.__name__: [
        c.name for c in MicrosoftImagesModel.unique_constraints()[0]]
}

def orm_update_table(db, provider, table_name, table_rows, version):
    if table_name == "regionmap":
        table_name_caps = "RegionMap"
        need_version = False
    else:
        table_name_caps = table_name.capitalize()
        need_version = True

    model = eval(f"{provider.capitalize()}{table_name_caps}Model")
    LOG.debug("Using model %s for provider %s table %s",
                 repr(model.__name__), repr(provider),
                 repr(table_name))

    # fields used to identify a matching existing entry
    identity_fields = IDENTITY_OVERRIDES.get(model.__name__, [])
    if identity_fields:
        LOG.debug("For %s using %s instead of primary key fields for "
                  "existing entry checking", repr(model.__name__),
                  repr(identity_fields))

    LOG.debug("Attempting to add %d new entries for model %s",
                 len(table_rows), repr(model.__name__))
    rows_added = 0
    rows_updated = 0
    for row_data in table_rows:
        # if identity_fields overrides have been specified use those
        # fields to construct the search_data that will be used to
        # check for existing matching entries, otherwise use the
        # fields that are marked as primary keys.
        if identity_fields:
            search_data = {k:row_data[k] for k in identity_fields}
        else:
            search_data = {k:v for k, v in row_data.items()
                               if getattr(model.__table__.columns,
                                          k).primary_key}

        # if no search_data was identified, fall back on doing a whole
        # row match search, to see if there is already an exact match
        # present.
        if not search_data:
            search_data = row_data

        LOG.debug("Checking for existing entries in %s using: %s",
                  repr(model.__name__),
                  repr(search_data))

        # if we find no match for the primary keys then add a new row
        found_row = db.query(model).filter_by(**search_data).one_or_none()
        if not found_row:
            row = model(**row_data)
            LOG.debug("Adding new row %s", repr(row))
            db.add(row)
            rows_added += 1
            continue

        # Now check if the found row is an exact match?
        if all([v == getattr(found_row, k)
                for k, v in row_data.items()]):
            LOG.debug("Skipping existing row: %s", repr(found_row))
            continue

        LOG.debug("Updating existing row: %s", repr(found_row))
        for k, v in row_data.items():
            setattr(found_row, k, v)
        rows_updated += 1


    if not rows_added and not rows_updated:
        LOG.info("No new entries found for model %s",
                    repr(model.__name__))
    else:
        if rows_added:
            LOG.info("Added %d entries for model %s",
                        rows_added, repr(model.__name__))

        if rows_updated:
            LOG.info("Updated %d entries for model %s",
                        rows_updated, repr(model.__name__))

        if need_version:
            # Lookup the existing version for the relevant table
            version_entry = db.query(VersionsModel).\
                               filter(VersionsModel.tablename==\
                                      model.__tablename__).\
                               one_or_none()
            # If we found an exiting entry then we need to update
            # the version value to reflect the incremental update.
            if version_entry:
                LOG.info("Updating %s table entry for table %s with "
                            "version %s", repr(VersionsModel.__tablename__),
                            repr(model.__tablename__), repr(version))
                # If the suggested version is >= the existing version
                # we can just use it, as this means that the associated
                # commit date stamp is newer than the previous one.
                if float(version_entry.version) < float(version):
                    version_entry.version = version
                else:
                    # If the existing version is newer than the suggested
                    # one, which could happen if there has already been
                    # an incremental update incorporated with the same
                    # commit date stamp, or if an older merge request was
                    # merged after a newer one, meaning that the most recent
                    # commit was from a previous date, then we just add 0.01
                    # to the existing version timestamp. This should allow us
                    # to support up to 100 incremental merges per day while
                    # maintaining the logical relationship between the commit
                    # date stamp and the version, and will still work for a
                    # higher incremental update rate, though the version value
                    # would roll over to the next logical "date" in such cases.
                    version_entry.version = float(version_entry.version) + 0.01
            else:
                # Otherwise we just add an initial version entry for
                # this table based on the supplied version, which is
                # derived from the commit date stamp.
                LOG.info("Adding %s table entry for table %s with "
                            "version %s", repr(VersionsModel.__tablename__),
                            repr(model.__tablename__), repr(version))
                db.add(VersionsModel(tablename=model.__tablename__,
                                     version=version))


def orm_update_tables(db, provider, tables, version):
    for table_name, table_rows in tables.items():
        if not table_rows:
            LOG.debug("Skipping table %s for provider %s; no entries "
                         "found", repr(table_name), repr(provider))
            continue
        orm_update_table(db, provider, table_name, table_rows, version)


def orm_load_database(pint_data, db_logfile=None):
    db = init_db(outputfile=db_logfile, create_all=False)

    data_files = gen_data_files_list(pint_data_repo=pint_data)

    # extract all the data from the data files
    data_store = {}
    for data_file in data_files:
        extract_data_from_file(data_file, data_store)

    # populate tables with data that was extracted
    for provider, provider_info in data_store.items():
        tables = provider_info['tables']
        version = provider_info['version']
        LOG.debug("%s: %s", provider.capitalize(), repr(tables.keys()))

        required_table_names = ['servers', 'images']
        if provider == "microsoft":
            required_table_names.append("regionmap")

        for table_name in required_table_names:
            if table_name not in tables:
                raise MissingRequiredTablesErrror(
                        "No %s table data for provider %s" %
                        (repr(table_name), repr(provider)))

        orm_update_tables(db, provider, tables, version)

    if db.new or db.dirty:
        LOG.debug("Added to the Database: %s", db.new)
        LOG.debug("Modified in the Database: %s", db.dirty)
        db.commit()


def create_db_uri(host, port, user, password, database, ssl_mode, root_cert):
    ssl_param = ''
    if ssl_mode:
        # see
        # https://www.postgresql.org/docs/11/libpq-connect.html#
        # LIBPQ-CONNECT-SSLMODE
        ssl_param = '?sslmode=%s' % (ssl_mode)
        if root_cert:
            ssl_param += '&sslrootcert=%s' % (root_cert)
    return f'postgresql://{user}:{password}@{host}:{port}/{database}{ssl_param}'


@click.group(help='Pint database update utility')
@click.option('-d', '--debug', help='Enable debugging', is_flag=True)
@click.option('-q', '--quiet',
              help='Minimises output unless --debug specified',
              is_flag=True)
@click.option('-h', '--host', help="Database host", required=True, type=str)
@click.option('-p', '--port', help="Database port", default=5432, type=int)
@click.option('-U', '--user', help="Database user", required=True, type=str)
@click.option('-W', '--password', help='Database password', required=True,
              hide_input=True, confirmation_prompt=True,
              prompt='Database Password')
@click.option('-n', '--database', help='Database name', default='postgres')
@click.option('--ssl-mode', help='Database SSL mode')
@click.option('--root-cert', help='Database root CA certificate file')
@click.pass_context
def pint_db(ctx, debug, quiet, host, port, user, password, database,
            ssl_mode, root_cert):
    if not any((debug, quiet)):
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    elif debug:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    ctx.obj['db_uri'] = create_db_uri(host, port, user, password, database,
                                      ssl_mode, root_cert)
    LOG.debug('db_uri: %s' % (ctx.obj['db_uri']))


@click.command(help='Update Pint data in the database.')
@click.option('--pint-data', help='Path to pint-data dir', type=str)
@click.option('--db-logfile', help='DB debug log file', default=None,
              required=False, type=str)
@click.pass_context
def update(ctx, pint_data, db_logfile):
    try:
        LOG.info('Updating data')
        # import data
        os.environ['DATABASE_URI'] = ctx.obj['db_uri']
        orm_load_database(pint_data, db_logfile=db_logfile)
        print('Pint database successfully updated.')
    except Exception as e:
        LOG.debug(e, exc_info=True)
        print('Failed to upgrade Pint database: %s' % (e))
        exit(1)


pint_db.add_command(update)


if __name__ == '__main__':
    pint_db()
