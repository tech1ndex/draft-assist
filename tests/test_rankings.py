"""Tests for the rankings module."""

import tempfile
from pathlib import Path

import pytest

from draft_assist.external.models import RankedPlayer
from draft_assist.rankings import RankingsManager
from draft_assist.settings import DraftSettings


@pytest.fixture
def sample_rankings_csv() -> str:
    """Sample rankings CSV content."""
    return """rank,name,position,team,notes
1,Patrick Mahomes,QB,KC,Elite QB
2,Travis Kelce,TE,KC,Top TE
3,Tyreek Hill,WR,MIA,Speed demon
4,Justin Jefferson,WR,MIN,Elite route runner
5,Christian McCaffrey,RB,SF,Versatile back
6,Josh Allen,QB,BUF,Dual threat
7,Davante Adams,WR,LV,Route master
8,Derrick Henry,RB,TEN,Workhorse
9,Stefon Diggs,WR,BUF,Reliable target
10,Austin Ekeler,RB,LAC,PPR machine
"""


@pytest.fixture
def rankings_file(sample_rankings_csv: str) -> Path:
    """Create a temporary rankings file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(sample_rankings_csv)
        return Path(f.name)


def test_load_rankings(rankings_file: Path) -> None:
    """Test loading rankings from CSV."""
    settings = DraftSettings(rankings_file_path=str(rankings_file))
    manager = RankingsManager(settings)

    players = manager.load_rankings()

    assert len(players) == 10
    assert players[0].name == "Patrick Mahomes"
    assert players[0].rank == 1
    assert players[0].position == "QB"


def test_get_player_by_rank(rankings_file: Path) -> None:
    """Test getting a player by rank."""
    settings = DraftSettings(rankings_file_path=str(rankings_file))
    manager = RankingsManager(settings)
    manager.load_rankings()

    player = manager.get_player_by_rank(3)

    assert player is not None
    assert player.name == "Tyreek Hill"


def test_get_player_by_name(rankings_file: Path) -> None:
    """Test getting a player by name."""
    settings = DraftSettings(rankings_file_path=str(rankings_file))
    manager = RankingsManager(settings)
    manager.load_rankings()

    player = manager.get_player_by_name("travis kelce")

    assert player is not None
    assert player.rank == 2


def test_get_players_by_position(rankings_file: Path) -> None:
    """Test filtering players by position."""
    settings = DraftSettings(rankings_file_path=str(rankings_file))
    manager = RankingsManager(settings)
    manager.load_rankings()

    wrs = manager.get_players_by_position("WR")

    assert len(wrs) == 4
    assert all(p.position == "WR" for p in wrs)


def test_get_top_available(rankings_file: Path) -> None:
    """Test getting top available players."""
    settings = DraftSettings(rankings_file_path=str(rankings_file))
    manager = RankingsManager(settings)
    manager.load_rankings()

    taken = {"Patrick Mahomes", "Travis Kelce"}
    available = manager.get_top_available(taken, count=3)

    assert len(available) == 3
    assert available[0].name == "Tyreek Hill"
    assert all(p.name not in taken for p in available)


def test_get_top_available_with_position_filter(rankings_file: Path) -> None:
    """Test getting top available players filtered by position."""
    settings = DraftSettings(rankings_file_path=str(rankings_file))
    manager = RankingsManager(settings)
    manager.load_rankings()

    taken = {"Christian McCaffrey"}
    available = manager.get_top_available(taken, count=2, position="RB")

    assert len(available) == 2
    assert all(p.position == "RB" for p in available)
    assert available[0].name == "Derrick Henry"


def test_get_best_available(rankings_file: Path) -> None:
    """Test getting single best available player."""
    settings = DraftSettings(rankings_file_path=str(rankings_file))
    manager = RankingsManager(settings)
    manager.load_rankings()

    best = manager.get_best_available(set())

    assert best is not None
    assert best.rank == 1


def test_load_missing_file() -> None:
    """Test loading from non-existent file."""
    settings = DraftSettings(rankings_file_path="/nonexistent/path.csv")
    manager = RankingsManager(settings)

    players = manager.load_rankings()

    assert players == []
