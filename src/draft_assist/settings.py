from functools import lru_cache
from pathlib import Path

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


class DraftSettings(BaseSettings):
    league_id: str = ""
    rankings_path: str = "rankings.csv"

    class Config:
        env_file = ".env"
        extra = "ignore"
        env_prefix = "DRAFT_"
        case_sensitive = False


@lru_cache
def get_draft_settings() -> DraftSettings:
    return DraftSettings()


def save_env_setting(key: str, value: str, env_file: Path = Path(".env")) -> None:
    key = key.upper()
    lines: list[str] = []
    found = False

    if env_file.exists():
        lines = env_file.read_text().splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            k = stripped.split("=", 1)[0].strip()
            if k == key:
                lines[i] = f"{key}={value}"
                found = True
                break

    if not found:
        lines.append(f"{key}={value}")

    env_file.write_text("\n".join(lines) + "\n")
