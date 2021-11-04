"""changeinfo urls end in slash

Revision ID: ee82c541fae0
Revises: e937749e3f8b
Create Date: 2021-12-02 11:25:41.279114

"""
import logging
import os

from alembic import op
import sqlalchemy as sa

# Leverage ORM for data update
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = 'ee82c541fae0'
down_revision = 'e937749e3f8b'
branch_labels = None
depends_on = None


# Get a logger to use for log messages
logger = logging.getLogger(os.path.basename(__file__))

#
# Define temporary ORM table definitions for the provider images
# tables that we can use to manipulate those tables.
#

Base = declarative_base()
class PintImagesTemp:
    changeinfo = sa.Column(sa.String(255))


class AlibabaImagesTemp(Base, PintImagesTemp):
    __tablename__ = 'alibabaimages'

    id = sa.Column(sa.String(100), primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    region = sa.Column(sa.String(100), nullable=False)


class AmazonImagesTemp(Base, PintImagesTemp):
    __tablename__ = 'amazonimages'

    id = sa.Column(sa.String(100), primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    region = sa.Column(sa.String(100), nullable=False)


class GoogleImagesTemp(Base, PintImagesTemp):
    __tablename__ = 'googleimages'

    name = sa.Column(sa.String(255), primary_key=True)
    project = sa.Column(sa.String(50), nullable=False)

class MicrosoftImagesTemp(Base, PintImagesTemp):
    __tablename__ = 'microsoftimages'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    environment = sa.Column(sa.String(50), nullable=False)


class OracleImagesTemp(Base, PintImagesTemp):
    __tablename__ = 'oracleimages'

    name = sa.Column(sa.String(255), nullable=False)
    id = sa.Column(sa.String(100), primary_key=True)


# All provider images tables
all_tables = [
    AlibabaImagesTemp,
    AmazonImagesTemp,
    GoogleImagesTemp,
    MicrosoftImagesTemp,
    OracleImagesTemp
]


def fixup_changeinfo_entries(db, tables):
    """Iterate over specified list of tables, checkling changeinfo entries
    to ensure they end with a '/', appending one if needed, and commit any
    changes at the end."""

    # list of possible fields that will be useful for identifying entries
    # that we may encounter, which will be included in the log message.
    reportable_fields = ['name', 'id', 'environment', 'project', 'region']

    # iterative over the specified tables
    for table in tables:

        # record the previous DB dirty entries count
        old_dirty = len(db.dirty)

        # iterate over all the rows in the table
        for row in db.query(table):
            # fix up any non-empty changeinfo entries to end with a '/'
            if row.changeinfo and not row.changeinfo.endswith('/'):
                row.changeinfo += '/'

                # log a message with meaningful identification info
                # to indicate that we fixed up the row's changeinfo
                fields = []
                for field in reportable_fields:
                    if hasattr(row, field):
                        value = getattr(row, field)
                        fields.append(f"{field}={value}")
                logger.debug('%s: %s - changedinfo fixed',
                             table.__tablename__,
                             ', '.join(fields))

        # determine how many entries were fixed
        fixed_entries = len(db.dirty) - old_dirty

        # if we fixed any entries, log a summary message with count
        if fixed_entries:
            logger.info('%s: Updated %d changeinfo entries', table.__tablename__, fixed_entries)

    # Commit any fixed changeinfo entries
    if db.dirty:
        logger.info('Committing %d changeinfo fixes', len(db.dirty))
        db.commit()


def upgrade():
    db = orm.Session(autocommit=False, autoflush=False,
                     bind=op.get_bind())

    # Ensure that all changeinfo entries end with a trailing
    # slash ('/') character.
    fixup_changeinfo_entries(db, all_tables)

    # No schema migration actions needed; we are just adding a new
    # validator to the model definitions, and fixing up existing
    # entries to match what the validator enforces.


def downgrade():
    # No schema changes to be rolled back, and retaining the added
    # trailing slash ('/') characters on changeinfo entries is not
    # going to negatively impact things if we do rollback.
    pass
