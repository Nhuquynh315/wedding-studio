from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Wedding Studio API"
    version: str = "0.1.0"

    database_url: str = "sqlite:///instance/wedding_studio.db"
    jwt_secret_key: str = "dev-only-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
