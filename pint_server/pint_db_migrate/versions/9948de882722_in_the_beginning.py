"""in the beginning

Revision ID: 9948de882722
Revises: 3a1b9b52bd78
Create Date: 2021-09-02 12:29:27.285358

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9948de882722'
down_revision = '3a1b9b52bd78'
branch_labels = None
depends_on = None

meta = sa.MetaData()

#
# Define the enumerations we need
#

# server_type is used in the *servers table
server_type = postgresql.ENUM('region', 'update', name='server_type',
                               metadata=meta)

# image_state is used in the *images table
image_state = postgresql.ENUM('deleted', 'deprecated', 'inactive',
                              'active', name='image_state',
                              metadata=meta)

# List of enums to be defined
enums_to_define = [server_type, image_state]

#
# Define common column definitions
#

# Images columns
images_name = sa.Column('name', sa.String(length=255), nullable=False)
images_state = sa.Column('state', image_state, nullable=True)
images_replacementname = sa.Column('replacementname', sa.String(length=255), nullable=True)
images_publishedon = sa.Column('publishedon', sa.Date(), nullable=False)
images_deprecatedon = sa.Column('deprecatedon', sa.Date(), nullable=True)
images_deletedon = sa.Column('deletedon', sa.Date(), nullable=True)
images_changeinfo = sa.Column('changeinfo', sa.String(length=255), nullable=True)
images_id = sa.Column('id', sa.String(length=100), nullable=False)
images_replacementid = sa.Column('replacementid', sa.String(length=100), nullable=True)

# Servers columns
servers_type = sa.Column('type', server_type, nullable=True)
servers_shape = sa.Column('shape', sa.String(length=10), nullable=True)
servers_name = sa.Column('name', sa.String(length=100), nullable=True)
servers_ip = sa.Column('ip', postgresql.INET(), nullable=False)

# Multi-table columns
common_region = sa.Column('region', sa.String(length=100), nullable=False)
common_environment = sa.Column('environment', sa.String(length=50), nullable=False)

#
# Define helper routines
#
def define_table(name, columns, primary_keys, meta=meta):
    """Define a table using copies of the supplied columns
    setting the primary_key attribute to true if the column
    name is in the primary_keys list, permitting the column
    definitions to be reused when defining multiple tables."""

    table_args = [name, meta]
    for orig_col in columns:
        col = orig_col.copy()

        if col.name in primary_keys:
            col.primary_key = True

        table_args.append(col)

    return sa.Table(*table_args)

#
# Define the tables we need
#

# Alibaba
alibabaimages = define_table(
    'alibabaimages',
    columns=[
        images_name,
        images_state,
        images_replacementname,
        images_publishedon,
        images_deprecatedon,
        images_deletedon,
        images_changeinfo,
        images_id,
        images_replacementid,
        sa.Column('region', sa.String(length=100), nullable=True)
    ],
    primary_keys=['name', 'publishedon', 'id']
)

alibaba_tables = [alibabaimages]

# Amazon
amazonimages = define_table(
    'amazonimages',
    columns=[
        images_name,
        images_state,
        images_replacementname,
        images_publishedon,
        images_deprecatedon,
        images_deletedon,
        images_changeinfo,
        images_id,
        images_replacementid,
        common_region
    ],
    primary_keys=['name', 'publishedon', 'id', 'region']
)

amazonservers = define_table(
    'amazonservers',
    columns=[
        servers_type,
        servers_shape,
        servers_name,
        servers_ip,
        common_region
    ],
    primary_keys=['ip', 'region']
)

amazon_tables = [amazonimages, amazonservers]

# Google
googleimages = define_table(
    'googleimages',
    columns=[
        images_name,
        images_state,
        images_replacementname,
        images_publishedon,
        images_deprecatedon,
        images_deletedon,
        images_changeinfo,
        sa.Column('project', sa.String(length=50), nullable=True)
     ],
    primary_keys=['name', 'publishedon']
)

googleservers = define_table(
    'googleservers',
    columns=[
        servers_type,
        servers_shape,
        servers_name,
        servers_ip,
        common_region
    ],
    primary_keys=['ip', 'region']
)

google_tables = [googleimages, googleservers]

# MicroSoft
microsoftimages = define_table(
    'microsoftimages',
    columns=[
        images_name,
        images_state,
        images_replacementname,
        images_publishedon,
        images_deprecatedon,
        images_deletedon,
        images_changeinfo,
        common_environment,
        sa.Column('urn', sa.String(length=100), nullable=True)
    ],
    primary_keys=['name', 'publishedon', 'environment']
)

microsoftregionmap = define_table(
    'microsoftregionmap',
    columns=[
        common_environment,
        common_region,
        sa.Column('canonicalname', sa.String(length=100), nullable=False)
    ],
    primary_keys=['environment', 'region', 'canonicalname']
)

microsoftservers = define_table(
    'microsoftservers',
    columns=[
        servers_type,
        servers_shape,
        servers_name,
        servers_ip,
        common_region
    ],
    primary_keys=['ip', 'region']
)

microsoft_tables = [microsoftimages, microsoftregionmap, microsoftservers]

# Oracle
oracleimages = define_table(
    'oracleimages',
    columns=[
        images_name,
        images_state,
        images_replacementname,
        images_publishedon,
        images_deprecatedon,
        images_deletedon,
        images_changeinfo,
        images_id,
        images_replacementid
    ],
    primary_keys=['name', 'publishedon', 'id']
)

oracle_tables = [oracleimages]

# Versions - used to track updates to provider specific tables
versions = define_table(
    'versions',
    columns=[
        sa.Column('tablename', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Numeric(), nullable=False)
    ],
    primary_keys=['tablename']
)

misc_tables = [versions]

# List of tables to be defined
tables_to_define = (alibaba_tables + amazon_tables + google_tables +
                    microsoft_tables + oracle_tables + misc_tables)


def upgrade():
    # create the above defined enums and tables if they don't already exist
    for obj in enums_to_define + tables_to_define:
        obj.create(op.get_bind(), checkfirst=True)


def downgrade():
    # drop the tables that were defined
    for table in enums_to_define + tables_to_define:
        op.drop_table(table.name)

    # drop the tables that were defined
    for enum in enums_to_define + tables_to_define:
        enum.drop(op.get_bind())
