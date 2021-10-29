"""microsoftimages unique constraint

Revision ID: 8c5fc3cd9b18
Revises: e2bdb3a5b1b4
Create Date: 2021-10-29 09:10:26.515096

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c5fc3cd9b18'
down_revision = 'e2bdb3a5b1b4'
branch_labels = None
depends_on = None


def upgrade():
    # Add a new unique constraint to the microsoft images table based upon
    # name and environment columns.
    op.create_unique_constraint(None, 'microsoftimages', ['name', 'environment'])


def downgrade():
    # remove the added unique constraint.
    op.drop_constraint(None, 'microsoftimages', type_='unique')
