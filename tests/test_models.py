"""Tests for the models module."""

from draft_assist.external.models import (
    DraftPick,
    DraftResult,
    League,
    Player,
    PlayerStatus,
    RankedPlayer,
    Team,
)


def test_player_creation() -> None:
    """Test creating a Player model."""
    player = Player(
        player_id="123",
        name="Patrick Mahomes",
        team="KC",
        position="QB",
        status=PlayerStatus.AVAILABLE,
    )

    assert player.player_id == "123"
    assert player.name == "Patrick Mahomes"
    assert player.status == PlayerStatus.AVAILABLE


def test_player_with_alias() -> None:
    """Test Player model with alias."""
    player = Player(player_id="456", name="Travis Kelce")

    assert player.player_id == "456"


def test_ranked_player() -> None:
    """Test RankedPlayer model."""
    player = RankedPlayer(
        rank=1,
        name="Patrick Mahomes",
        position="QB",
        team="KC",
        notes="Elite QB",
    )

    assert player.rank == 1
    assert player.notes == "Elite QB"


def test_league() -> None:
    """Test League model."""
    league = League(
        league_id="123.l.456",
        name="Test League",
        num_teams=12,
        draft_status="predraft",
    )

    assert league.league_id == "123.l.456"
    assert league.num_teams == 12


def test_team_with_roster() -> None:
    """Test Team model with roster."""
    players = [
        Player(player_id="1", name="Player 1"),
        Player(player_id="2", name="Player 2"),
    ]
    team = Team(
        team_id="123.l.456.t.1",
        name="My Team",
        roster=players,
    )

    assert len(team.roster) == 2


def test_draft_pick() -> None:
    """Test DraftPick model."""
    pick = DraftPick(
        pick_number=1,
        round_number=1,
        team_id="123.l.456.t.1",
        player=Player(player_id="789", name="Patrick Mahomes"),
    )

    assert pick.pick_number == 1
    assert pick.player is not None
    assert pick.player.name == "Patrick Mahomes"


def test_draft_result_success() -> None:
    """Test successful DraftResult."""
    result = DraftResult(
        success=True,
        message="Draft pick successful",
        player=Player(player_id="123", name="Test Player"),
        pick_number=5,
    )

    assert result.success is True
    assert result.pick_number == 5


def test_draft_result_failure() -> None:
    """Test failed DraftResult."""
    result = DraftResult(
        success=False,
        message="Player already drafted",
    )

    assert result.success is False
    assert result.player is None
