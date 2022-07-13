"""changeinfo validation

Revision ID: b5fc4b5d23b1
Revises: ee82c541fae0
Create Date: 2021-11-03 08:07:49.484934

"""
import logging
import os

from alembic import op
import sqlalchemy as sa

# Leverage ORM for data update
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = 'b5fc4b5d23b1'
down_revision = 'ee82c541fae0'
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


# Subset of images tables that have regions
region_tables = [
    AlibabaImagesTemp,
    AmazonImagesTemp
]


def validate_changeinfo_region_associations(db, tables):
    """Iterate over specific DB tables, ensuring that changeinfo entries
    exist for all regions, or no regions, for all image names."""

    # track a list of image names with problems for each table that we
    # are checking.
    problems = {}

    # check each table in turn
    for table in tables:
        problem_names = []

        # iterate over the distinct names in the table
        for name in [r.name for r in db.query(table.name).
                                        distinct(table.name).all()]:
            # retrieve the region and changeinfo entries for name
            region_changeinfo = [r for r in db.query(table.region,
                                                     table.changeinfo).
                                               filter(table.name == name).
                                               all()]

            # extract those entries where changeinfo is Null or empty
            no_changeinfo = [r for r in region_changeinfo
                             if not r.changeinfo]

            # if the Null/empty changeinfo list is a non-empty subset
            if ((len(no_changeinfo) > 0) and
                (len(no_changeinfo) < len(region_changeinfo))):
                # log a warning to document the problem entry and add
                # the name to the list of problem names for this table.
                logger.warning("%s: %s no changeinfo provided for "
                               "these %s out of %d regions: %s",
                               table.__tablename__, name,
                               len(no_changeinfo), len(region_changeinfo),
                               [r.region for r in no_changeinfo])
                problem_names.append(name)

        # if there were problem names, record them for this table
        if problem_names:
            problems[table.__tablename__] = problem_names

    # if problems were detected, raise a ValueError exception with the
    # list of tables for which problems occurred.
    if problems:
        raise ValueError(f"Not all regions have changeinfo entries in %s" %
                         repr(list(problems.keys())))


def upgrade():
    db = orm.Session(autocommit=False, autoflush=False,
                     bind=op.get_bind())

    # Ensure that all existing tables either have a changeinfo
    # set for all of the regions, or none of the regions, that
    # are associated with a given image
    validate_changeinfo_region_associations(db, region_tables)

    # No schema migration actions needed; we are just adding a new
    # validation to the flush handling for the model definitions.

def downgrade():
    # No schema changes to be rolled back.
    pass
