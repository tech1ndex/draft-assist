from pathlib import Path
from unittest.mock import patch

from draft_assist.settings import DraftSettings, YahooSettings, save_env_setting


def test_yahoo_settings_defaults():
    with patch.dict("os.environ", {}, clear=True):
        settings = YahooSettings(_env_file=None)
    assert settings.redirect_uri == "https://localhost:8888"
    assert settings.access_token == ""
    assert settings.refresh_token == ""
    assert settings.client_id == ""
    assert settings.client_secret == ""
    assert "fantasysports.yahooapis.com" in str(settings.api_url)


def test_draft_settings_defaults():
    with patch.dict("os.environ", {}, clear=True):
        settings = DraftSettings(_env_file=None)
    assert settings.league_id == ""
    assert settings.rankings_path == "rankings.csv"


def test_draft_settings_rankings_path_from_env():
    with patch.dict(
        "os.environ", {"DRAFT_RANKINGS_PATH": "/custom/path.csv"}, clear=True
    ):
        settings = DraftSettings(_env_file=None)
    assert settings.rankings_path == "/custom/path.csv"


def test_draft_settings_from_env():
    with patch.dict("os.environ", {"DRAFT_LEAGUE_ID": "423.l.12345"}, clear=True):
        settings = DraftSettings(_env_file=None)
    assert settings.league_id == "423.l.12345"


def test_save_env_setting_new_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    save_env_setting("DRAFT_LEAGUE_ID", "423.l.99", env_file=env_file)
    assert "DRAFT_LEAGUE_ID=423.l.99" in env_file.read_text()


def test_save_env_setting_update_existing(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("YAHOO_CLIENT_ID=abc\nDRAFT_LEAGUE_ID=old_value\nOTHER=keep\n")
    save_env_setting("DRAFT_LEAGUE_ID", "new_value", env_file=env_file)
    content = env_file.read_text()
    assert "DRAFT_LEAGUE_ID=new_value" in content
    assert "YAHOO_CLIENT_ID=abc" in content
    assert "OTHER=keep" in content
    assert "old_value" not in content


def test_save_env_setting_append_to_existing(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("YAHOO_CLIENT_ID=abc\n")
    save_env_setting("DRAFT_LEAGUE_ID", "423.l.99", env_file=env_file)
    content = env_file.read_text()
    assert "YAHOO_CLIENT_ID=abc" in content
    assert "DRAFT_LEAGUE_ID=423.l.99" in content
