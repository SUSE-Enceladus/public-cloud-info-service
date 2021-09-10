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

from alembic import command
from alembic.config import Config
from urllib.parse import quote_plus
import click
import logging
import sys


LOG = logging.getLogger(__name__)


def create_db_uri(host, port, user, password, database, ssl_mode, root_cert):
    ssl_param = ''
    if ssl_mode:
        # see
        # https://www.postgresql.org/docs/11/libpq-connect.html#
        # LIBPQ-CONNECT-SSLMODE
        ssl_param = '?sslmode=%s' % (ssl_mode)
        if root_cert:
            ssl_param += '&sslrootcert=%s' % (root_cert)

    # NOTE(gyee): we must escape percent (%) characters as Python ConfigParser,
    # which uses by Alembic to manage configuration options, is treating
    # it as a format string instead of raw string.
    # See https://github.com/sqlalchemy/alembic/issues/700
    password = quote_plus(password).replace('%', '%%')

    return f'postgresql://{user}:{password}@{host}:{port}/{database}{ssl_param}'


def get_alembic_config(repository, db_uri):
    alembic_cfg = Config()
    alembic_cfg.set_main_option('script_location', repository)
    alembic_cfg.set_main_option('sqlalchemy.url', db_uri)
    return alembic_cfg


@click.group(help='Pint database management utility')
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
@click.option('--repository', help='Database migration project repository',
              required=True, type=str)
@click.pass_context
def pint_db(ctx, debug, quiet, host, port, user, password, database,
            ssl_mode, root_cert, repository):
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
    ctx.obj['repository'] = repository
    LOG.debug('db_uri: %s' % (ctx.obj['db_uri']))
    LOG.debug('repository: %s' % (ctx.obj['repository']))


@click.command(help='Print database version')
@click.pass_context
def db_version(ctx):
    print('Current Version')
    print('===============')
    command.current(get_alembic_config(
        ctx.obj['repository'], ctx.obj['db_uri']))


@click.command(help='Upgrade database schema')
@click.pass_context
def upgrade(ctx):
    try:
        LOG.info('Creating version control')
        LOG.info('Upgrading schema')
        command.upgrade(get_alembic_config(
            ctx.obj['repository'], ctx.obj['db_uri']), 'head')
        print('Pint database schema migration successfully completed.')
    except Exception as e:
        LOG.debug(e, exc_info=True)
        print('Failed to upgrade Pint database: %s' % (e))


pint_db.add_command(db_version)
pint_db.add_command(upgrade)


if __name__ == '__main__':
    pint_db()
