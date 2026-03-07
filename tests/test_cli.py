from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from draft_assist.cli.main import app

runner = CliRunner()


@patch("draft_assist.cli.main.get_yahoo_settings")
@patch("draft_assist.cli.main.YahooFantasyClient")
def test_auth_browser_success(mock_client_cls, mock_settings):
    mock_client = MagicMock()
    mock_client.authenticate_via_browser.return_value = True
    mock_client.access_token = "test_access"
    mock_client.refresh_token = "test_refresh"
    mock_client_cls.return_value = mock_client
    mock_settings.return_value = MagicMock()

    result = runner.invoke(app, ["auth"])
    assert result.exit_code == 0
    assert "YAHOO_ACCESS_TOKEN=test_access" in result.output
    assert "YAHOO_REFRESH_TOKEN=test_refresh" in result.output


@patch("draft_assist.cli.main.get_yahoo_settings")
@patch("draft_assist.cli.main.YahooFantasyClient")
def test_auth_browser_runtime_error(mock_client_cls, mock_settings):
    mock_client = MagicMock()
    mock_client.authenticate_via_browser.side_effect = RuntimeError("browser failed")
    mock_client_cls.return_value = mock_client
    mock_settings.return_value = MagicMock()

    result = runner.invoke(app, ["auth"])
    assert result.exit_code == 1


@patch("draft_assist.cli.main.logger")
@patch("draft_assist.cli.main.YahooFantasyClient")
def test_leagues_not_authenticated(mock_client_cls, mock_logger):
    mock_client = MagicMock()
    mock_client.is_authenticated = False
    mock_client_cls.return_value = mock_client

    result = runner.invoke(app, ["leagues"])
    assert result.exit_code == 1
    mock_logger.error.assert_called_once_with(
        "Not authenticated. Run 'draft-assist auth' first."
    )
