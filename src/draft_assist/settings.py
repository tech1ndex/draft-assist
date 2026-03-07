from functools import lru_cache

from pydantic_settings import BaseSettings


class YahooSettings(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "https://localhost:8888"
    access_token: str = ""
    refresh_token: str = ""
    api_url: str = "https://fantasysports.yahooapis.com/fantasy/v2"
    token_url: str = "https://api.login.yahoo.com/oauth2/get_token"  # noqa: S105
    oauth_base_url: str = "https://api.login.yahoo.com/oauth2"

    class Config:
        env_file = ".env"
        extra = "ignore"
        env_prefix = "YAHOO_"
        case_sensitive = False


@lru_cache
def get_yahoo_settings() -> YahooSettings:
    return YahooSettings()
