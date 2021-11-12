"""image dates validation

Revision ID: 14ae3b1b5e81
Revises: 8c5fc3cd9b18
Create Date: 2021-11-10 10:25:52.824012

"""
import logging
import os

from alembic import op
import sqlalchemy as sa

# Leverage ORM for data update
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = '14ae3b1b5e81'
down_revision = '8c5fc3cd9b18'
branch_labels = None
depends_on = None

# Get a logger to use for log messages
logger = logging.getLogger(os.path.basename(__file__))

#
# Define temporary ORM table definitions for the tables that
# we can use to manipulate those tables.
#

Base = declarative_base()

class PintImagesTemp:
    publishedon = sa.Column(sa.Date, nullable=False)
    deprecatedon = sa.Column(sa.Date)
    deletedon = sa.Column(sa.Date)


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


all_tables = [
    AlibabaImagesTemp,
    AmazonImagesTemp,
    GoogleImagesTemp,
    MicrosoftImagesTemp,
    OracleImagesTemp
]


def validate_image_date_fields(db, tables):
    """Iterate over specified images tables in the DB, ensuring that for
    all entries, the 3 date fields, namely publishedon, deprecatedon and
    deletedon, when set, satisfy the requirement of
        publishedon <= deprecatedon <= deletedon."""

    # track list of rows with problems for each table that being checked.
    problems = {}

    row_id_fields = ['name', 'id', 'region', 'environment', 'project']

    # check each table in turn
    for table in tables:
        problem_rows = []

        # iterate over all rows of the table
        for row in db.query(table).all():
            row_problems = 0

            # construct a row identifier from the list of fields that may
            # possibly exist for the table's rows
            row_identifier = " ".join(["%s=%s" % (f, repr(getattr(row, f)))
                                       for f in row_id_fields
                                       if hasattr(row, f)])

            if row.deprecatedon and row.deprecatedon < row.publishedon:
                logger.warning('%s: [%s] - publishedon(%s) should not be '
                               'after deprecatedon(%s)',
                               table.__tablename__,
                               row_identifier,
                               row.publishedon,
                               row.deprecatedon)
                row_problems += 1

            if row.deletedon and row.deletedon < row.publishedon:
                logger.warning('%s: [%s] - publishedon(%s) should not be '
                               'after deletedon(%s)',
                               table.__tablename__,
                               row_identifier,
                               row.publishedon,
                               row.deletedon)
                row_problems += 1

            if row.deprecatedon and row.deletedon and row.deletedon < row.deprecatedon:
                logger.warning('%s: [%s] - deprecatedon(%s) should not be '
                               'after deletedon(%s)',
                               table.__tablename__,
                               row_identifier,
                               row.publishedon,
                               row.deletedon)
                row_problems += 1

            if row_problems > 0:
                problem_rows.append(row)

        # if there were problem rows, record them for this table
        if problem_rows:
            problems[table.__tablename__] = problem_rows

    # if problems were detected, raise a ValueError exception with the
    # list of tables for which problems occurred.
    if problems:
        raise ValueError(f"Not all images have valid date settings in %s" %
                         repr(list(problems.keys())))


def upgrade():
    db = orm.Session(autocommit=False, autoflush=False,
                     bind=op.get_bind())

    # Validate the image date fields for all existing images tables
    validate_image_date_fields(db, all_tables)

    # Not schema migrations to be performed.
    pass


def downgrade():
    # Not schema migrations to be rolled back.
    pass
