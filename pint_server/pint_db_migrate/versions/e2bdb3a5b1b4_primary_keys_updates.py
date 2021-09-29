"""primary keys updates

Revision ID: e2bdb3a5b1b4
Revises: 528cb85d6ad3
Create Date: 2021-09-10 04:05:03.540503

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import Sequence, CreateSequence

# revision identifiers, used by Alembic.
revision = 'e2bdb3a5b1b4'
down_revision = '528cb85d6ad3'
branch_labels = None
depends_on = None

meta = sa.MetaData()

#
# Define the types we need
#

# image_state is an enumeration type used in the *images tables
image_state = postgresql.ENUM('deleted', 'deprecated', 'inactive', 'active', name='image_state')

# image_region is a string type used in many of the alibaba and amazon images tables
image_region = sa.VARCHAR(length=100)

# image_project is a string type used in the googleimages table
image_project = sa.VARCHAR(length=50)

# server_ip is a Postgres INET type used in the *servers tables
server_ip = postgresql.INET()

# server_name is a string type used in the *servers table
server_name = sa.VARCHAR(length=100)

# server_type is an enumeration type used in the *servers table
server_type = postgresql.ENUM('region', 'update', name='server_type',
                               metadata=meta)

#
# Define a dictionary of tables to process, with the table name as
# key, and entries indicating whether to:
#   * create a sequence
#   * update columns
#   * change the keys
#
#

# All of the servers tables are being changed in the same way,
# so define a common servers data entry to specify the set of
# of changes that will be made.
servers_data = {
    "seq_column": "id",
    "columns": {
        "ip" : {
            "type": server_ip,
            "nullable": {
                "new": True,
                "old": False
            }
        },
        "type" : {
            "type": server_type,
            "nullable": {
                "new": False,
                "old": True
            }
        },
    },
    "keys": {
        "old": ["ip", "region"],
        "new": ["id"]
    }
}

# The dictionary tracking the changes we want to make to the tables
table_data = {
    "alibabaimages" : {
        "columns": {
            "region": {
                "type": image_region,
                "nullable": {
                    "old": True,
                    "new": False
                }
            },
            "state": {
                "type": image_state,
                "nullable": {
                    "old": True,
                    "new": False
                }
            }
        },
        "keys": {
            "old": ["name", "publishedon", "id"],
            "new": ["id"]
        }
    },
    "amazonimages" : {
        "columns": {
            "region": {
                "type": image_region,
                "nullable": {
                    "old": True,
                    "new": False
                }
            },
            "state": {
                "type": image_state,
                "nullable": {
                    "old": True,
                    "new": False
                }
            }
        },
        "keys": {
            "old": ["name", "publishedon", "id", "region"],
            "new": ["id"]
        }
    },
    "amazonservers": servers_data,
    "googleimages" : {
        "columns": {
            "project": {
                "type": image_project,
                "nullable": {
                    "old": True,
                    "new": False
                }
            },
            "state": {
                "type": image_state,
                "nullable": {
                    "old": True,
                    "new": False
                }
            }
        },
        "keys": {
            "old": ["name", "publishedon"],
            "new": ["name"]
        }
    },
    "googleservers": servers_data,
    "microsoftimages": {
        "seq_column": "id",
        "columns": {
            "state": {
                "type": image_state,
                "nullable": {
                    "old": True,
                    "new": False
                }
            }
        },
        "keys": {
            "old": ["name", "publishedon", "environment"],
            "new": ["id"]
        }
    },
    "microsoftregionmap": {
        "keys": {
            "old": ["environment", "region", "canonicalname"],
            "new": ["region"]
        }
    },
    "microsoftservers": servers_data,
    "oracleimages": {
        "columns": {
            "state": {
                "type": image_state,
                "nullable": {
                    "old": True,
                    "new": False
                }
            }
        },
        "keys": {
            "old": ["name", "publishedon", "id"],
            "new": ["id"]
        }
    }
}

# Upgrade a table using the supplied table info
def table_upgrade(table_name, table_info):
    columns = table_info.get('columns')
    keys = table_info.get('keys')
    seq_column = table_info.get('seq_column')

    # Delete the old primary key if one was specified
    if keys:
        op.drop_constraint('%s_pkey' % table_name, table_name, type_='primary')

    # Create a sequence and add associated column if specified
    if seq_column:
        seq = Sequence('%s_%s_seq' % (table_name, seq_column))
        op.execute(CreateSequence(seq))
        op.add_column(table_name, sa.Column(seq_column, sa.Integer(), server_default=seq.next_value(), nullable=False))

    # Apply the new column settings if specified
    if columns:
        for column_name, column_info in columns.items():
            op.alter_column(table_name, column_name,
                            existing_type=column_info['type'],
                            nullable=column_info['nullable']['new'])

    # Create the new primary key if one was specified
    if keys:
        op.create_primary_key('%s_pkey' % table_name, table_name, keys['new'])


# Downgrade a table using the supplied table info
def table_downgrade(table_name, table_info):
    columns = table_info.get('columns')
    keys = table_info.get('keys')
    seq_column = table_info.get('seq_column')

    # Delete the new primary key if one was specified
    if keys:
        op.drop_constraint('%s_pkey' % table_name, table_name, type_='primary')

    # Restore the original column settings if specified
    if columns:
        for column_name, column_info in columns.items():
            op.alter_column(table_name, column_name,
                            existing_type=column_info['type'],
                            nullable=column_info['nullable']['old'])

    # Delete the sequence column and associated sequence if specified
    if seq_column:
        op.drop_column(table_name, seq_column)
        op.execute('drop sequence %s_id_seq' % (table_name))

    # Restore the old primary key if one was specified
    if keys:
        op.create_primary_key('%s_pkey' % table_name, table_name, keys['old'])


def upgrade():
    for table_name, table_info in table_data.items():
        table_upgrade(table_name, table_info)


def downgrade():
    for table_name, table_info in table_data.items():
        table_upgrade(table_name, table_info)
