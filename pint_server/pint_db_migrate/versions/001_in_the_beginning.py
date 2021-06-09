# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

from sqlalchemy import (Table, Column, Date, Integer, Numeric,
                        String, MetaData, Enum)
from sqlalchemy.dialects import postgresql


meta = MetaData()

server_type = postgresql.ENUM('region', 'update', name='server_type',
                               metadata=meta)

image_state = postgresql.ENUM('deleted', 'deprecated', 'inactive',
                              'active', name='image_state', metadata=meta)

amazonimages = Table(
    'amazonimages', meta,
    Column('name', String(255), primary_key=True),
    Column('state', image_state),
    Column('replacementname', String(255)),
    Column('publishedon', Date, primary_key=True),
    Column('deprecatedon', Date),
    Column('deletedon', Date),
    Column('changeinfo', String(255)),

    Column('id', String(100), primary_key=True),
    Column('replacementid', String(100)),
    Column('region', String(100), primary_key=True),
)

alibabaimages = Table(
    'alibabaimages', meta,
    Column('name', String(255), primary_key=True),
    Column('state', image_state),
    Column('replacementname', String(255)),
    Column('publishedon', Date, primary_key=True),
    Column('deprecatedon', Date),
    Column('deletedon', Date),
    Column('changeinfo', String(255)),

    Column('id', String(100), primary_key=True),
    Column('replacementid', String(100)),
    Column('region', String(100)),
)

googleimages = Table(
    'googleimages', meta,
    Column('name', String(255), primary_key=True),
    Column('state', image_state),
    Column('replacementname', String(255)),
    Column('publishedon', Date, primary_key=True),
    Column('deprecatedon', Date),
    Column('deletedon', Date),
    Column('changeinfo', String(255)),

    Column('project', String(50)),
)

microsoftimages = Table(
    'microsoftimages', meta,
    Column('name', String(255), primary_key=True),
    Column('state', image_state),
    Column('replacementname', String(255)),
    Column('publishedon', Date, primary_key=True),
    Column('deprecatedon', Date),
    Column('deletedon', Date),
    Column('changeinfo', String(255)),

    Column('environment', String(50), primary_key=True),
    Column('urn', String(100))
)

amazonservers = Table(
    'amazonservers', meta,
    Column('type', server_type),
    Column('shape', String(10)),
    Column('name', String(100)),
    Column('ip', postgresql.INET, primary_key=True),
    Column('region', String(100), primary_key=True),
)

googleservers = Table(
    'googleservers', meta,
    Column('type', server_type),
    Column('shape', String(10)),
    Column('name', String(100)),
    Column('ip', postgresql.INET, primary_key=True),
    Column('region', String(100), primary_key=True),
)

microsoftservers = Table(
    'microsoftservers', meta,
    Column('type', server_type),
    Column('shape', String(10)),
    Column('name', String(100)),
    Column('ip', postgresql.INET, primary_key=True),
    Column('region', String(100), primary_key=True),
)

microsoftregionmap = Table(
    'microsoftregionmap', meta,
    Column('environment', String(50), primary_key=True),
    Column('region', String(100), primary_key=True),
    Column('canonicalname', String(100), primary_key=True),
)

versions = Table(
    'versions', meta,
    Column('tablename', String(100), primary_key=True),
    Column('version', Numeric, nullable=False),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    amazonimages.create(checkfirst=True)
    alibabaimages.create(checkfirst=True)
    googleimages.create(checkfirst=True)
    microsoftimages.create(checkfirst=True)
    amazonservers.create(checkfirst=True)
    googleservers.create(checkfirst=True)
    microsoftservers.create(checkfirst=True)
    microsoftregionmap.create(checkfirst=True)
    versions.create(checkfirst=True)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    amazonimages.drop()
    alibabaimages.drop()
    googleimages.drop()
    microsoftimages.drop()
    amazonservers.drop()
    googleservers.drop()
    microsoftservers.drop()
    microsoftregionmap.drop()
    versions.drop()

