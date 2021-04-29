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

# NOTE(gyee):
# see https://flask.palletsprojects.com/en/1.1.x/patterns/sqlalchemy/

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pint_server.models import (
        AlibabaImagesModel,
        AmazonImagesModel,
        AmazonServersModel,
        Base,
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


def get_environ_or_bust(key_name):
    assert key_name in os.environ, 'Environment variable %s is required.' % (
        key_name)
    return os.environ.get(key_name)


def create_postgres_url_from_env():
    db_user = get_environ_or_bust('POSTGRES_USER')
    db_password = get_environ_or_bust('POSTGRES_PASSWORD')
    db_name = get_environ_or_bust('POSTGRES_DB')
    db_host = get_environ_or_bust('POSTGRES_HOST')
    db_port = os.environ.get('POSTGRES_PORT', 5432)
    db_ssl_mode = os.environ.get('POSTGRES_SSL_MODE', None)
    db_root_cert = os.environ.get('POSTGRES_SSL_ROOT_CERTIFICATE', None)
    ssl_mode = ''
    if db_ssl_mode:
        # see
        # https://www.postgresql.org/docs/11/libpq-connect.html#
        # LIBPQ-CONNECT-SSLMODE
        ssl_mode = '?sslmode=%s' % (db_ssl_mode)
        if db_root_cert:
            ssl_mode += '&sslrootcert=%s' % (db_root_cert)

    return ('postgresql://%(user)s:%(password)s@%(host)s:%(port)s/'
            '%(db)s%(ssl)s' % {
                'user': db_user,
                'password': db_password,
                'db': db_name,
                'host': db_host,
                'port': db_port,
                'ssl': ssl_mode})


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()

    if os.environ.get('DATABASE_URI', None):
        engine = create_engine(os.environ['DATABASE_URI'],
                               convert_unicode=True)
    else:
        engine = create_engine(
            create_postgres_url_from_env(), convert_unicode=True)

    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Base.query = db_session.query_property()

    Base.metadata.create_all(bind=engine)

    return db_session
