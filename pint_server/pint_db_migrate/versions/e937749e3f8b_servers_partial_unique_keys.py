"""servers partial unique keys

Revision ID: e937749e3f8b
Revises: 14ae3b1b5e81
Create Date: 2021-11-16 06:24:00.605747

"""
import logging
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e937749e3f8b'
down_revision = '14ae3b1b5e81'
branch_labels = None
depends_on = None

logger = logging.getLogger(os.path.basename(__file__))

#
# Helper Methods
#
def report_duplicates(table, fields, _log=logger.warning):
    """Generate an SQL query string of the format

        SELECT table.field[0], table.field[1], ..., table.fields[n]
        FROM table
        GROUP BY table.field[0], table.field[1], ..., table.fields[n]
        HAVING count(table.fields[0]) > 1

    and use that to determine if any duplicates exist, reporting any
    found via the specified logger."""

    # Generate a list of '{table}.{field}' entries for unique fields,
    # and comma joined string from that list
    unique_fields = [f'{table}.{f}' for f in fields]
    joined_unique_fields = ', '.join(unique_fields)

    # Generate a list of strings that will be joined with
    query_elements = []

    # Add the SELECT statement for specified table_fields
    query_elements.append(f'SELECT {joined_unique_fields}')

    # Add the FROM statement specifying the table
    query_elements.append(f'FROM {table}')

    # Add the GROUP BY statement for specified the table fields
    query_elements.append(f'GROUP BY {joined_unique_fields}')

    # Add the HAVING count() check for the first unique field
    query_elements.append(f'HAVING count({unique_fields[0]}) > 1')

    # Generate an SQL text object for the proposed query string
    duplicates_query = sa.text(' '.join(query_elements))

    logger.debug('Duplicates Query: %s', duplicates_query)

    # Check for duplicates
    conn = op.get_bind()
    duplicates = conn.execute(duplicates_query).fetchall()

    if duplicates:
        # Report the duplicates that were found
        _log('Duplicates detected in %s:', table)
        for row in duplicates:
            _log('    %s', repr({f: row[i] for i, f in enumerate(fields)}))


#
# Define appropriate per table unique entry checks for ip and ipv6 addresses
#
unique_server_addresses_checks = [
    ["amazonservers", ['ip']],
    ["amazonservers", ['ipv6']],
    ["googleservers", ['ip']],
    ["googleservers", ['ipv6']],
    ["microsoftservers", ['ip', 'region']],
    ["microsoftservers", ['ipv6', 'region']],
]

def upgrade():

    # Check for and warn about any duplicates that may exist in the servers tables
    for table, fields in unique_server_addresses_checks:
        report_duplicates(table, fields)

    # Add the unique indices; will fail if duplicates exist
    for table, fields in unique_server_addresses_checks:
        op.create_index(f'uix_{table}_{fields[0]}_not_null', table, fields, unique=True, postgresql_where=sa.text(f'{fields[0]} IS NOT NULL'))


def downgrade():
    # Drop the unique indices
    for table, fields in reversed(unique_server_addresses_checks):
        op.drop_index(f'uix_{table}_{fields[0]}_not_null', table_name=table, postgresql_where=sa.text(f'{fields[0]} IS NOT NULL'))
