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
import logging

from sqlalchemy import Column, Date, Enum, Integer, Numeric, String, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import validates


logger = logging.getLogger(__name__)

Base = declarative_base()


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

    @classmethod
    def unique_constraints(cls):
        """Return the table's unique constraint's column names, or empty list."""
        return [u for u in cls.__table__.constraints
                if isinstance(u, UniqueConstraint)]

    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__,
                             ", ".join(["%s=%s" % (k, repr(getattr(self, k)))
                                        for k in self.__table__.
                                        columns.keys()]))


class ProviderImageBase(PintBase):
    state = Column(Enum(ImageState, name=ImageState.__enum_name__),
                   nullable=False)
    replacementname = Column(String(255))
    publishedon = Column(Date, nullable=False)
    deprecatedon = Column(Date)
    deletedon = Column(Date)
    changeinfo = Column(String(255))

    @validates('publishedon', 'deprecatedon', 'deletedon')
    def validate_image_dates(self, key, value):
        publishedon = value if key == 'publishedon' else self.publishedon
        deprecatedon = value if key == 'deprecatedon' else self.deprecatedon
        deletedon = value if key == 'deletedon' else self.deletedon

        # If called for deprecatedon or deletedon before publishedon
        # has been set we have nothing to compare against, so just
        # fall through and accept the provided value for now.
        # Since the validator will be triggered for all 3 fields and
        # performs the same checks each time, even if publishedon is
        # the last field we are called for, the validator will still
        # fail if either deprecatedon or deletedon is not valid with
        # respect to that publishedon value.
        if publishedon:
            if deprecatedon and deprecatedon < publishedon:
                raise ValueError('Image %s invalid dates specified - '
                                 'publishedon(%s) should not be after '
                                 'deprecatedon(%s)' % (self.name,
                                 str(publishedon), str(deprecatedon)))

            if deletedon and deletedon < publishedon:
                raise ValueError('Image %s invalid dates specified - '
                                 'publishedon(%s) should not be after '
                                 'deletedon(%s)' % (self.name,
                                 str(publishedon), str(deletedon)))

        if deprecatedon and deletedon and deletedon < deprecatedon:
            raise ValueError('Image %s invalid dates specified - '
                             'deprecatedon(%s) should not be after '
                             'deletedon(%s)' % (self.name,
                             str(deprecatedon), str(deletedon)))

        return value


    @validates("changeinfo")
    def validate_changeinfo(self, key, value):
        if value and not value.endswith('/'):
            value = value + '/'
            logger.info('%s.%s = %s (updated)', self.tablename, key, repr(value))

        return value


class ProviderServerBase(PintBase):
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(ServerType, name=ServerType.__enum_name__),
                  nullable=False)
    shape = Column(String(10))
    name = Column(String(100))

    @validates("name")
    def validate_name(self, key, value):
        if self.type == ServerType.update:
            if not value:
                raise ValueError("%s.%s cannot be null/empty for an update server." % (self.tablename, key))
        return value


class AmazonImagesModel(Base, ProviderImageBase):
    __tablename__ = 'amazonimages'

    name = Column(String(255), nullable=False)
    cspname = Column(String(128), nullable=True)
    id = Column(String(100), primary_key=True)
    replacementid = Column(String(100))
    region = Column(String(100), nullable=False)


class AlibabaImagesModel(Base, ProviderImageBase):
    __tablename__ = 'alibabaimages'

    name = Column(String(255), nullable=False)
    id = Column(String(100), primary_key=True)
    replacementid = Column(String(100))
    region = Column(String(100), nullable=False)


class GoogleImagesModel(Base, ProviderImageBase):
    __tablename__ = 'googleimages'

    name = Column(String(255), primary_key=True)
    project = Column(String(50), nullable=False)


class MicrosoftImagesModel(Base, ProviderImageBase):
    __tablename__ = 'microsoftimages'
    __table_args__ = (UniqueConstraint('name', 'environment'),)

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    environment = Column(String(50), nullable=False)
    urn = Column(String(100))


class OracleImagesModel(Base, ProviderImageBase):
    __tablename__ = 'oracleimages'

    name = Column(String(255), nullable=False)
    id = Column(String(100), primary_key=True)
    replacementid = Column(String(100))


class AmazonServersModel(Base, ProviderServerBase):
    __tablename__ = 'amazonservers'

    # NOTE(gyee): the INET type is specific to PostgreSQL. If in the future
    # we decided to support other vendors, we'll need to update this
    # column type accordingly.
    ip = Column(postgresql.INET)
    region = Column(String(100), nullable=False)
    ipv6 = Column(postgresql.INET)

    __table_args__ = (
        Index('uix_amazonservers_region_ip_not_null', 'region', 'ip', unique=True, postgresql_where=ip.isnot(None)),
        Index('uix_amazonservers_region_ipv6_not_null', 'region', 'ipv6', unique=True, postgresql_where=ipv6.isnot(None)),
    )


class GoogleServersModel(Base, ProviderServerBase):
    __tablename__ = 'googleservers'

    # NOTE(gyee): the INET type is specific to PostgreSQL. If in the future
    # we decided to support other vendors, we'll need to update this
    # column type accordingly.
    ip = Column(postgresql.INET)
    region = Column(String(100), nullable=False)
    ipv6 = Column(postgresql.INET)

    __table_args__ = (
        Index('uix_googleservers_region_ip_not_null', 'region', 'ip', unique=True, postgresql_where=ip.isnot(None)),
        Index('uix_googleservers_region_ipv6_not_null', 'region', 'ipv6', unique=True, postgresql_where=ipv6.isnot(None)),
    )


class MicrosoftServersModel(Base, ProviderServerBase):
    __tablename__ = 'microsoftservers'

    # NOTE(gyee): the INET type is specific to PostgreSQL. If in the future
    # we decided to support other vendors, we'll need to update this
    # column type accordingly.
    ip = Column(postgresql.INET)
    region = Column(String(100), nullable=False)
    ipv6 = Column(postgresql.INET)

    __table_args__ = (
        Index('uix_microsoftservers_region_ip_not_null', 'region', 'ip', unique=True, postgresql_where=ip.isnot(None)),
        Index('uix_microsoftservers_region_ipv6_not_null', 'region', 'ipv6', unique=True, postgresql_where=ipv6.isnot(None)),
    )


class MicrosoftRegionMapModel(Base, PintBase):
    __tablename__ = 'microsoftregionmap'

    environment = Column(String(50), primary_key=True)
    region = Column(String(100), primary_key=True)
    canonicalname = Column(String(100), primary_key=True)


class VersionsModel(Base, PintBase):
    __tablename__ = 'versions'

    tablename = Column(String(100), primary_key=True)
    version = Column(Numeric, nullable=False)
