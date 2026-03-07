from unittest.mock import patch

from draft_assist.settings import YahooSettings


def test_yahoo_settings_defaults():
    with patch.dict("os.environ", {}, clear=True):
        settings = YahooSettings(_env_file=None)
    assert settings.redirect_uri == "https://localhost:8888"
    assert settings.access_token == ""
    assert settings.refresh_token == ""
    assert settings.client_id == ""
    assert settings.client_secret == ""
    assert "fantasysports.yahooapis.com" in str(settings.api_url)
