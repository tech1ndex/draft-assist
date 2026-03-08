from unittest.mock import MagicMock, patch

import pytest
import requests

from draft_assist.external.yahoo import YahooFantasyClient
from draft_assist.settings import YahooSettings

YAHOO_ENV_KEYS = [
    "YAHOO_CLIENT_ID",
    "YAHOO_CLIENT_SECRET",
    "YAHOO_REDIRECT_URI",
    "YAHOO_ACCESS_TOKEN",
    "YAHOO_REFRESH_TOKEN",
    "YAHOO_API_URL",
]


@pytest.fixture(autouse=True)
def _clean_yahoo_env(monkeypatch):
    for key in YAHOO_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def yahoo_settings():
    return YahooSettings(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="https://localhost:8888",
        _env_file=None,
    )


def test_init_no_tokens(yahoo_settings):
    client = YahooFantasyClient(yahoo_settings)
    assert client._access_token is None
    assert client._refresh_token is None
    assert not client.is_authenticated


def test_init_loads_tokens_from_settings():
    settings = YahooSettings(
        client_id="id",
        client_secret="secret",
        access_token="my_access",
        refresh_token="my_refresh",
    )
    client = YahooFantasyClient(settings)
    assert client._access_token == "my_access"
    assert client._refresh_token == "my_refresh"
    assert client.is_authenticated


def test_get_auth_url(yahoo_settings):
    client = YahooFantasyClient(yahoo_settings)
    url = client.get_auth_url()
    assert "client_id=test_client_id" in url
    assert "redirect_uri=" in url
    assert "response_type=code" in url
    assert "scope=fspt-r" in url


@patch("draft_assist.external.yahoo.requests.post")
def test_authenticate_success(mock_post, yahoo_settings):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "new_access",
        "refresh_token": "new_refresh",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    client = YahooFantasyClient(yahoo_settings)
    result = client.authenticate("auth_code_123")

    assert result is True
    assert client._access_token == "new_access"
    assert client._refresh_token == "new_refresh"


@patch("draft_assist.external.yahoo.requests.post")
def test_authenticate_failure(mock_post, yahoo_settings):
    mock_post.side_effect = requests.RequestException("connection error")

    client = YahooFantasyClient(yahoo_settings)
    result = client.authenticate("bad_code")

    assert result is False
    assert client._access_token is None


@patch("draft_assist.external.yahoo.requests.post")
def test_refresh_access_token_success(mock_post, yahoo_settings):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "refreshed_access",
        "refresh_token": "refreshed_refresh",
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    client = YahooFantasyClient(yahoo_settings)
    client._refresh_token = "existing_refresh"
    result = client.refresh_access_token()

    assert result is True
    assert client._access_token == "refreshed_access"


def test_refresh_access_token_no_refresh_token(yahoo_settings):
    client = YahooFantasyClient(yahoo_settings)
    assert client._refresh_token is None
    assert client.refresh_access_token() is False


def test_is_authenticated(yahoo_settings):
    client = YahooFantasyClient(yahoo_settings)
    assert not client.is_authenticated

    client._access_token = "some_token"
    assert client.is_authenticated


def test_get_headers_raises_when_not_authenticated(yahoo_settings):
    client = YahooFantasyClient(yahoo_settings)
    with pytest.raises(ValueError, match="Not authenticated"):
        client._get_headers()


def test_get_headers_returns_bearer_token(yahoo_settings):
    client = YahooFantasyClient(yahoo_settings)
    client._access_token = "my_token"
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer my_token"
    assert headers["Content-Type"] == "application/json"


@patch("draft_assist.external.yahoo.YahooFantasyClient.authenticate")
@patch("draft_assist.external.yahoo.YahooFantasyClient._wait_for_auth_code")
@patch("draft_assist.external.yahoo.webbrowser.open")
def test_authenticate_via_browser(mock_browser, mock_wait, mock_auth, yahoo_settings):
    mock_wait.return_value = "browser_auth_code"
    mock_auth.return_value = True

    client = YahooFantasyClient(yahoo_settings)
    result = client.authenticate_via_browser()

    assert result is True
    mock_browser.assert_called_once()
    mock_wait.assert_called_once()
    mock_auth.assert_called_once_with("browser_auth_code")


def test_parse_draft_results_empty():
    response = {"fantasy_content": {"league": [{}]}}
    result = YahooFantasyClient._parse_draft_results(response)
    assert result == []


def test_parse_draft_results_predraft_empty_list():
    response = {
        "fantasy_content": {
            "league": [{"league_key": "469.l.9760"}, {"draft_results": []}]
        }
    }
    result = YahooFantasyClient._parse_draft_results(response)
    assert result == []


def test_parse_draft_results_with_picks():
    """Yahoo nests player data under a numeric key inside draft_result."""
    response = {
        "fantasy_content": {
            "league": [
                {"league_key": "469.l.9760"},
                {
                    "draft_results": {
                        "0": {
                            "draft_result": {
                                "pick": 1,
                                "round": 1,
                                "team_key": "469.l.9760.t.6",
                                "player_key": "469.p.11731",
                                "0": {
                                    "players": {
                                        "0": {
                                            "player": [
                                                [
                                                    {"player_key": "469.p.11731"},
                                                    {
                                                        "name": {
                                                            "full": "Gunnar Henderson"
                                                        }
                                                    },
                                                ]
                                            ]
                                        }
                                    }
                                },
                            }
                        },
                        "1": {
                            "draft_result": {
                                "pick": 2,
                                "round": 1,
                                "team_key": "469.l.9760.t.3",
                                "player_key": "469.p.60419",
                                "0": {
                                    "players": {
                                        "0": {
                                            "player": [
                                                [
                                                    {"player_key": "469.p.60419"},
                                                    {"name": {"full": "Paul Skenes"}},
                                                ]
                                            ]
                                        }
                                    }
                                },
                            }
                        },
                        "count": 2,
                    }
                },
            ]
        }
    }
    picks = YahooFantasyClient._parse_draft_results(response)
    assert len(picks) == 2
    assert picks[0].pick == 1
    assert picks[0].player_name == "Gunnar Henderson"
    assert picks[0].team_key == "469.l.9760.t.6"
    assert picks[1].pick == 2
    assert picks[1].player_name == "Paul Skenes"


@patch("draft_assist.external.oauth_server.wrap_socket_ssl")
def test_wait_for_auth_code_timeout(mock_ssl, yahoo_settings):
    mock_ssl.side_effect = lambda sock: sock  # skip SSL wrapping

    client = YahooFantasyClient(yahoo_settings)
    with pytest.raises(RuntimeError, match="timed out"):
        client._wait_for_auth_code(port=18899, timeout=1)


@patch("draft_assist.external.oauth_server.wrap_socket_ssl")
def test_wait_for_auth_code_error_param(mock_ssl, yahoo_settings):
    import threading
    import urllib.request

    mock_ssl.side_effect = lambda sock: sock

    client = YahooFantasyClient(yahoo_settings)

    def send_error_request():
        import time

        time.sleep(0.5)
        urllib.request.urlopen("http://localhost:18900/?error=access_denied", timeout=2)

    t = threading.Thread(target=send_error_request)
    t.start()

    with pytest.raises(RuntimeError, match="OAuth error"):
        client._wait_for_auth_code(port=18900, timeout=5)

    t.join(timeout=3)
