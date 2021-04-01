import enum
import os

from pint_server.app import db


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


class ProviderImageBase(object):
    name = db.Column(db.String(255))
    state = db.Column(db.Enum(ImageState))
    replacementname = db.Column(db.String(255))
    publishedon = db.Column(db.Date)
    deprecatedon = db.Column(db.Date)
    deletedon = db.Column(db.Date)
    changeinfo = db.Column(db.String(255))


class ProviderServerBase(object):
    type = db.Column(db.Enum(ServerType))
    name = db.Column(db.String(100))
    ip = db.Column(db.String(15), primary_key=True)
    region = db.Column(db.String(100))


class AmazonImagesModel(db.Model, ProviderImageBase):
    __tablename__ = 'amazonimages'

    id = db.Column(db.String(100), primary_key=True)
    replacementid = db.Column(db.String(100))
    region = db.Column(db.String(100))


class AlibabaImagesModel(db.Model, ProviderImageBase):
    __tablename__ = 'alibabaimages'

    id = db.Column(db.String(100), primary_key=True)
    replacementid = db.Column(db.String(100))
    region = db.Column(db.String(100))


class GoogleImagesModel(db.Model, ProviderImageBase):
    __tablename__ = 'googleimages'

    name = db.Column(db.String(255), primary_key=True)
    project = db.Column(db.String(50))


class MicrosoftImagesModel(db.Model, ProviderImageBase):
    __tablename__ = 'microsoftimages'

    name = db.Column(db.String(255), primary_key=True)
    environment = db.Column(db.String(50))
    urn = db.Column(db.String(100))


class OracleImagesModel(db.Model, ProviderImageBase):
    __tablename__ = 'oracleimages'

    id = db.Column(db.String(100), primary_key=True)
    replacementid = db.Column(db.String(100))


class AmazonServersModel(db.Model,  ProviderServerBase):
    __tablename__ = 'amazonservers'


class GoogleServersModel(db.Model,  ProviderServerBase):
    __tablename__ = 'googleservers'


class MicrosoftServersModel(db.Model, ProviderServerBase):
    __tablename__ = 'microsoftservers'


class AzureEnvironmentsModel(db.Model):
    __tablename__ = 'azureenvironments'

    version = db.Column(db.Date)
    environment = db.Column(db.String(100), primary_key=True)
    region = db.Column(db.String(100), primary_key=True)
    alternatename = db.Column(db.String(100), primary_key=True)

class VersionsModel(db.Model):
    __tablename__ = 'versions'

    amazonservers = db.Column(db.Numeric, primary_key=True)
    amazonimages = db.Column(db.Numeric)
    googleservers = db.Column(db.Numeric)
    googleimages = db.Column(db.Numeric)
    oracleimages = db.Column(db.Numeric)
    microsoftservers = db.Column(db.Numeric)
    microsoftimages = db.Column(db.Numeric)
    alibabaimages = db.Column(db.Numeric)
