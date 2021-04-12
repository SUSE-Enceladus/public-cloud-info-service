# NOTE(gyee): see https://flask.palletsprojects.com/en/1.1.x/patterns/sqlalchemy/

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


def get_environ_or_bust(key_name):
    assert key_name in os.environ, 'Environment variable %s is required.' % (
        key_name)
    return os.environ.get(key_name)


def create_postgres_url_from_env():
    db_user = get_environ_or_bust('POSTGRES_USER')
    db_password = get_environ_or_bust('POSTGRES_PASSWORD')
    db_name = get_environ_or_bust('POSTGRES_DB')
    db_host = get_environ_or_bust('POSTGRES_HOST')
    db_ssl_mode = os.environ.get('POSTGRES_SSL_MODE', None)
    db_root_cert = os.environ.get('POSTGRES_SSL_ROOT_CERTIFICATE', None)
    ssl_mode = ''
    if db_ssl_mode:
        # see https://www.postgresql.org/docs/11/libpq-connect.html#LIBPQ-CONNECT-SSLMODE
        ssl_mode = '?sslmode=%s' % (db_ssl_mode)
        if db_root_cert:
            ssl_mode += '&sslrootcert=%s' % (db_root_cert)

    return 'postgresql://%(user)s:%(password)s@%(host)s:5432/%(db)s%(ssl)s' % {
        'user': db_user,
        'password': db_password,
        'db': db_name,
        'host': db_host,
        'ssl': ssl_mode}


if os.environ.get('DATABASE_URI', None):
    engine = create_engine(os.environ['DATABASE_URI'], convert_unicode=True)
else:
    # FIXME(gyee): assume PostgresSQL URI for now. Otherwise, we'll need
    # to use 'DATABASE_URI' instead.
    engine = create_engine(
        create_postgres_url_from_env(), convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    #from pint_server.models import ImageState, AmazonImagesModel, \
    #                               OracleImagesModel, \
    #                               AlibabaImagesModel, MicrosoftImagesModel, \
    #                               GoogleImagesModel, AmazonServersModel, \
    #                               MicrosoftServersModel, GoogleServersModel, \
    #                               ServerType, VersionsModel, \
    #                               MicrosoftRegionMapModel
    Base.metadata.create_all(bind=engine)
