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

import enum

from sqlalchemy import Column, Date, Enum, Numeric, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql


Base = declarative_base()
# from pint_server.database import Base


class ImageState(enum.Enum):
    __enum_name__ = 'image_state'

    deleted = 'deleted'
    deprecated = 'deprecated'
    inactive = 'inactive'
    active = 'active'

    def __str__(self):
        return str(self.value)


class ServerType(enum.Enum):
    __enum_name__ = 'server_type'

    region = 'region'
    update = 'update'


class PintBase(object):
    @property
    def tablename(self):
        """Return table name."""
        return self.__tablename__

    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__,
                             ", ".join(["%s=%s" % (k, repr(getattr(self, k)))
                                        for k in self.__table__.
                                        columns.keys()]))


class ProviderImageBase(PintBase):
    name = Column(String(255), primary_key=True)
    state = Column(Enum(ImageState, name=ImageState.__enum_name__))
    replacementname = Column(String(255))
    publishedon = Column(Date, primary_key=True)
    deprecatedon = Column(Date)
    deletedon = Column(Date)
    changeinfo = Column(String(255))


class ProviderServerBase(PintBase):
    type = Column(Enum(ServerType, name=ServerType.__enum_name__), nullable=False)
    shape = Column(String(10))
    name = Column(String(100), nullable=False)
    # NOTE(gyee): the INET type is specific to PostgreSQL. If in the future
    # we decided to support other vendors, we'll need to update this
    # column type accordingly.
    ip = Column(postgresql.INET, primary_key=True)
    region = Column(String(100), primary_key=True)
    ipv6 = Column(postgresql.INET)


class AmazonImagesModel(Base, ProviderImageBase):
    __tablename__ = 'amazonimages'

    id = Column(String(100), primary_key=True)
    replacementid = Column(String(100))
    region = Column(String(100), primary_key=True)


class AlibabaImagesModel(Base, ProviderImageBase):
    __tablename__ = 'alibabaimages'

    id = Column(String(100), primary_key=True)
    replacementid = Column(String(100))
    region = Column(String(100))


class GoogleImagesModel(Base, ProviderImageBase):
    __tablename__ = 'googleimages'

    project = Column(String(50))


class MicrosoftImagesModel(Base, ProviderImageBase):
    __tablename__ = 'microsoftimages'

    environment = Column(String(50), primary_key=True)
    urn = Column(String(100))


class OracleImagesModel(Base, ProviderImageBase):
    __tablename__ = 'oracleimages'

    id = Column(String(100), primary_key=True)
    replacementid = Column(String(100))


class AmazonServersModel(Base, ProviderServerBase):
    __tablename__ = 'amazonservers'


class GoogleServersModel(Base, ProviderServerBase):
    __tablename__ = 'googleservers'


class MicrosoftServersModel(Base, ProviderServerBase):
    __tablename__ = 'microsoftservers'


class MicrosoftRegionMapModel(Base, PintBase):
    __tablename__ = 'microsoftregionmap'

    environment = Column(String(50), primary_key=True)
    region = Column(String(100), primary_key=True)
    canonicalname = Column(String(100), primary_key=True)


class VersionsModel(Base, PintBase):
    __tablename__ = 'versions'

    tablename = Column(String(100), primary_key=True)
    version = Column(Numeric, nullable=False)
