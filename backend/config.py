import os
import warnings

from dotenv import load_dotenv

load_dotenv()

_SECRET_KEY_FALLBACK = "dev-only-secret-do-not-use-in-production"


class Config:
    """Base configuration"""

    if not os.getenv("SECRET_KEY"):
        warnings.warn(
            "SECRET_KEY is not set — falling back to an insecure dev default. "
            "Set SECRET_KEY in your environment before deploying.",
            stacklevel=2,
        )
    SECRET_KEY = os.getenv("SECRET_KEY") or _SECRET_KEY_FALLBACK
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///wedding_studio.db")


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_RECORD_QUERIES = True


class TestingConfig(Config):
    """Testing configuration"""

    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ["SECRET_KEY"]  # must be set — crashes loudly if missing
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]  # must be set


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
