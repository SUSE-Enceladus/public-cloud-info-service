import enum
import os

from app import db


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
    version = db.Column(db.Numeric)
    name = db.Column(db.String(255))
    state = db.Column(db.Enum(ImageState))
    replacementname = db.Column(db.String(255))
    publishedon = db.Column(db.Date)
    deprecatedon = db.Column(db.Date)
    deletedon = db.Column(db.Date)
    changeinfo = db.Column(db.String(255))


class ProviderServerBase(object):
    version = db.Column(db.Date)
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


# FIXME(gyee): this table is currently broken. Need to
# fix the import script
class AlibabaServersModel(db.Model):
    __tablename__ = 'alibabaservers'

    version = db.Column(db.Date, primary_key=True)


class GoogleServersModel(db.Model,  ProviderServerBase):
    __tablename__ = 'googleservers'


class MicrosoftServersModel(db.Model, ProviderServerBase):
    __tablename__ = 'microsoftservers'


# FIXME(gyee): this table is currently broken. Need to
# fix the import script
class OracleServersModel(db.Model):
    __tablename__ = 'oracleservers'

    version = db.Column(db.Date, primary_key=True)


class AzureEnvironmentsModel(db.Model):
    __tablename__ = 'azureenvironments'

    version = db.Column(db.Date)
    environment = db.Column(db.String(100), primary_key=True)
    region = db.Column(db.String(100), primary_key=True)
    alternatename = db.Column(db.String(100), primary_key=True)
