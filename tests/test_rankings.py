from pathlib import Path

import pytest

from draft_assist.rankings import RankingsManager

CSV_CONTENT = """rank,name,position,team,notes
1,Patrick Mahomes,QB,KC,Elite
2,Josh Allen,QB,BUF,Dual threat
3,Saquon Barkley,RB,PHI,
4,Breece Hall,RB,NYJ,Bounce back
5,Ja'Marr Chase,WR,CIN,
6,Tyreek Hill,WR,MIA,Speed
7,Travis Kelce,TE,KC,GOAT TE
8,CeeDee Lamb,WR,DAL,
9,Bijan Robinson,RB,ATL,
10,Lamar Jackson,QB,BAL,MVP
"""


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    p = tmp_path / "rankings.csv"
    p.write_text(CSV_CONTENT)
    return p


def test_load_csv(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    players = manager.get_best_available(limit=100)
    assert len(players) == 10
    assert players[0].rank == 1
    assert players[-1].rank == 10


def test_get_best_available(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    top3 = manager.get_best_available(limit=3)
    assert len(top3) == 3
    assert [p.rank for p in top3] == [1, 2, 3]


def test_get_best_available_by_position(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    qbs = manager.get_best_available(position="QB", limit=10)
    assert len(qbs) == 3
    assert all(p.player.position == "QB" for p in qbs)


def test_get_best_available_limit(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    result = manager.get_best_available(limit=2)
    assert len(result) == 2


def test_get_player(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    player = manager.get_player("Patrick Mahomes")
    assert player is not None
    assert player.rank == 1
    assert player.player.position == "QB"
    assert player.notes == "Elite"


def test_get_player_case_insensitive(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    player = manager.get_player("patrick mahomes")
    assert player is not None
    assert player.player.name == "Patrick Mahomes"


def test_get_player_not_found(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    assert manager.get_player("Nobody Real") is None


def test_mark_taken_removes_from_best_available(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    manager.mark_taken("Patrick Mahomes")
    players = manager.get_best_available(limit=100)
    assert len(players) == 9
    assert all(p.player.name != "Patrick Mahomes" for p in players)


def test_mark_taken_case_insensitive(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    manager.mark_taken("PATRICK MAHOMES")
    players = manager.get_best_available(limit=100)
    assert all(p.player.name != "Patrick Mahomes" for p in players)


def test_get_player_still_works_after_mark_taken(csv_path: Path) -> None:
    manager = RankingsManager(csv_path)
    manager.mark_taken("Patrick Mahomes")
    player = manager.get_player("Patrick Mahomes")
    assert player is not None
    assert player.rank == 1


def test_load_csv_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        RankingsManager(Path("/nonexistent/rankings.csv"))
