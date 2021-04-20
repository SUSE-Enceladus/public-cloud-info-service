import enum

from sqlalchemy import Column, Date, Enum, Numeric, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
# from pint_server.database import Base


class ImageState(enum.Enum):
    deleted = 'deleted'
    deprecated = 'deprecated'
    inactive = 'inactive'
    active = 'active'

    def __str__(self):
        return str(self.value)


class ServerType(enum.Enum):
    region = 'region'
    update = 'update'


class PintBase(object):
    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__,
                             ", ".join(["%s=%s" % (k, repr(getattr(self, k)))
                                        for k in self.__table__.
                                        columns.keys()]))


class ProviderImageBase(PintBase):
    name = Column(String(255), primary_key=True)
    state = Column(Enum(ImageState))
    replacementname = Column(String(255))
    publishedon = Column(Date, primary_key=True)
    deprecatedon = Column(Date)
    deletedon = Column(Date)
    changeinfo = Column(String(255))


class ProviderServerBase(PintBase):
    type = Column(Enum(ServerType))
    name = Column(String(100))
    ip = Column(String(15), primary_key=True)
    region = Column(String(100), primary_key=True)


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

    name = Column(String(255), primary_key=True)
    project = Column(String(50))


class MicrosoftImagesModel(Base, ProviderImageBase):
    __tablename__ = 'microsoftimages'

    name = Column(String(255), primary_key=True)
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
