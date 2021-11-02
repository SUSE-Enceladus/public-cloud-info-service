"""microsoftimages unique constraint

Revision ID: 8c5fc3cd9b18
Revises: e2bdb3a5b1b4
Create Date: 2021-10-29 09:10:26.515096

"""
import os
import logging

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c5fc3cd9b18'
down_revision = 'e2bdb3a5b1b4'
branch_labels = None
depends_on = None

logger = logging.getLogger(os.path.basename(__file__))

#
# Unique constraint definition settings
#
uc_table = 'microsoftimages'
uc_fields = ['name', 'environment']

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
        _log('Duplicates detected in microsoftimages:')
        for row in duplicates:
            _log('    %s', repr(dict(name=row[0], environment=row[1])))


#
# Mainline migration entry points
#
def upgrade():
    # Check for and report any duplicates found for the fields in the
    # proposed unique constraint
    report_duplicates(uc_table, uc_fields)

    # Add a new unique constraint to the 'microsoftimages' table based
    # upon the name and environment columns.
    op.create_unique_constraint(None, uc_table, uc_fields)


def downgrade():
    # remove the added unique constraint.
    op.drop_constraint(None, uc_table, type_='unique')
