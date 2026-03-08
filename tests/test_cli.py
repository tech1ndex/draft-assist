from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from draft_assist.cli.main import app
from draft_assist.external.models import League

runner = CliRunner()

CSV_CONTENT = """rank,name,position,team,notes
1,Patrick Mahomes,QB,KC,Elite
2,Josh Allen,QB,BUF,Dual threat
3,Saquon Barkley,RB,PHI,
4,Breece Hall,RB,NYJ,Bounce back
5,Ja'Marr Chase,WR,CIN,
"""


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


@patch("draft_assist.cli.league.get_yahoo_settings")
@patch("draft_assist.cli.league.YahooFantasyClient")
def test_league_list_not_authenticated(mock_client_cls, mock_settings):
    mock_client = MagicMock()
    mock_client.is_authenticated = False
    mock_client_cls.return_value = mock_client
    mock_settings.return_value = MagicMock()

    result = runner.invoke(app, ["league", "show"])
    assert result.exit_code == 1


@patch("draft_assist.cli.league.save_env_setting")
@patch("draft_assist.cli.league.get_yahoo_settings")
@patch("draft_assist.cli.league.YahooFantasyClient")
def test_league_set_success(mock_client_cls, mock_settings, mock_save):
    mock_client = MagicMock()
    mock_client.is_authenticated = True
    mock_client.get_league.return_value = League(
        league_id="423.l.123",
        name="Test League",
        num_teams=12,
        draft_status="predraft",
        current_week=0,
        season=2026,
    )
    mock_client_cls.return_value = mock_client
    mock_settings.return_value = MagicMock()

    result = runner.invoke(app, ["league", "use", "423.l.123"])
    assert result.exit_code == 0
    mock_save.assert_called_once_with("DRAFT_LEAGUE_ID", "423.l.123")


@patch("draft_assist.cli.league.get_yahoo_settings")
@patch("draft_assist.cli.league.YahooFantasyClient")
def test_league_set_not_authenticated(mock_client_cls, mock_settings):
    mock_client = MagicMock()
    mock_client.is_authenticated = False
    mock_client_cls.return_value = mock_client
    mock_settings.return_value = MagicMock()

    result = runner.invoke(app, ["league", "use", "423.l.123"])
    assert result.exit_code == 1


@patch("draft_assist.cli.league.get_yahoo_settings")
@patch("draft_assist.cli.league.YahooFantasyClient")
def test_league_set_league_not_found(mock_client_cls, mock_settings):
    mock_client = MagicMock()
    mock_client.is_authenticated = True
    mock_client.get_league.return_value = None
    mock_client_cls.return_value = mock_client
    mock_settings.return_value = MagicMock()

    result = runner.invoke(app, ["league", "use", "423.l.999"])
    assert result.exit_code == 1


def _write_csv(tmp_path: Path) -> Path:
    p = tmp_path / "rankings.csv"
    p.write_text(CSV_CONTENT)
    return p


@patch("draft_assist.cli.draft.get_draft_settings")
def test_draft_rankings(mock_settings, tmp_path: Path):
    csv_path = _write_csv(tmp_path)
    mock_settings.return_value = MagicMock(rankings_path=str(csv_path))

    result = runner.invoke(app, ["draft", "rankings"])
    assert result.exit_code == 0
    assert "Patrick Mahomes" in result.output
    assert "Rankings" in result.output


@patch("draft_assist.cli.draft.get_draft_settings")
def test_draft_rankings_position_filter(mock_settings, tmp_path: Path):
    csv_path = _write_csv(tmp_path)
    mock_settings.return_value = MagicMock(rankings_path=str(csv_path))

    result = runner.invoke(app, ["draft", "rankings", "--position", "QB"])
    assert result.exit_code == 0
    assert "Patrick Mahomes" in result.output
    assert "Josh Allen" in result.output
    assert "Saquon Barkley" not in result.output


@patch("draft_assist.cli.draft.get_draft_settings")
def test_draft_available(mock_settings, tmp_path: Path):
    csv_path = _write_csv(tmp_path)
    mock_settings.return_value = MagicMock(rankings_path=str(csv_path))

    result = runner.invoke(app, ["draft", "available"])
    assert result.exit_code == 0
    assert "Best Available" in result.output
    assert "Patrick Mahomes" in result.output


@patch("draft_assist.cli.draft.get_draft_settings")
def test_draft_rankings_file_not_found(mock_settings):
    mock_settings.return_value = MagicMock(rankings_path="/nonexistent/file.csv")

    result = runner.invoke(app, ["draft", "rankings"])
    assert result.exit_code == 1


@patch("draft_assist.cli.draft.get_draft_settings")
@patch("draft_assist.cli.draft.get_yahoo_settings")
@patch("draft_assist.cli.draft.YahooFantasyClient")
def test_draft_live_no_league_id(
    mock_client_cls, mock_yahoo_settings, mock_draft_settings
):
    mock_client = MagicMock()
    mock_client.is_authenticated = True
    mock_client_cls.return_value = mock_client
    mock_yahoo_settings.return_value = MagicMock()
    mock_draft_settings.return_value = MagicMock(
        league_id="", rankings_path="rankings.csv"
    )

    result = runner.invoke(app, ["draft", "live"])
    assert result.exit_code == 1


@patch("draft_assist.cli.draft.time.sleep", side_effect=KeyboardInterrupt)
@patch("draft_assist.cli.draft.get_draft_settings")
@patch("draft_assist.cli.draft.get_yahoo_settings")
@patch("draft_assist.cli.draft.YahooFantasyClient")
def test_draft_live_keyboard_interrupt(
    mock_client_cls,
    mock_yahoo_settings,
    mock_draft_settings,
    _mock_sleep,  # noqa: PT019
    tmp_path: Path,
):
    csv_path = _write_csv(tmp_path)
    mock_client = MagicMock()
    mock_client.is_authenticated = True
    mock_client.get_draft_results.return_value = []
    mock_client_cls.return_value = mock_client
    mock_yahoo_settings.return_value = MagicMock()
    mock_draft_settings.return_value = MagicMock(
        league_id="423.l.123", rankings_path=str(csv_path)
    )

    result = runner.invoke(app, ["draft", "live"])
    assert result.exit_code == 0
    assert "Draft tracking stopped." in result.output
