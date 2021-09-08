"""Add IPv6 column

Revision ID: 528cb85d6ad3
Revises: 3a1b9b52bd78
Create Date: 2021-07-30 19:05:31.695486

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '528cb85d6ad3'
down_revision = '9948de882722'
branch_labels = None
depends_on = None

# Servers tables to be updated
servers_tables = ["amazonservers", "googleservers", "microsoftservers"]

# Define new ipv6 column to be added to servers tables
ipv6 = sa.Column('ipv6', postgresql.INET(), nullable=True)

def upgrade():
    # add the new ipv6 column to the relevant tables
    for table_name in servers_tables:
        op.add_column(table_name, ipv6)


def downgrade():
    # remove the ipv6 column from the relevant tables
    for table_name in servers_tables:
        op.drop_column(table_name, ipv6.name)
