import os

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ['SECRET_KEY']
    ADMIN_PWD = os.environ['ADMIN_PWD']
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    S3_OR_DBX = os.environ['S3_OR_DBX']
    if S3_OR_DBX == 'S3':
        S3_BUCKET = os.environ['S3_BUCKET']
    if S3_OR_DBX == 'DBX':
        DROPBOX_KEY = os.environ['DROPBOX_KEY']

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
