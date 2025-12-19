import os
from datetime import timedelta

# Try to import `config` from python-decouple. If that fails (wrong env, different
# package, or running without the venv), provide a minimal fallback that reads
# from environment variables so the app still runs.
try:
    from decouple import config
except Exception:
    def config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            try:
                value = cast(value)
            except Exception:
                pass
        return value

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

class Config:
    SECRET_KEY = config('SECRET_KEY', default='ceclol')
    JWT_SECRET_KEY = config('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)

class DevConfig(Config):
    DEBUG = config('DEBUG', default=True, cast=bool)
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "db.sqlite3")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = config('DEBUG', default=True, cast=bool)

class ProdConfig(Config):
    DEBUG = config('DEBUG', default=False, cast=bool)
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  

config_dict = {
    'dev': DevConfig,
    'prod': ProdConfig,
    'test': TestConfig
}