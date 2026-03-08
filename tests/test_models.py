from draft_assist.external.models import DraftPick, League, Player, RankedPlayer


def test_league() -> None:
    league = League(
        league_id="123.l.456",
        name="Test League",
        num_teams=12,
        draft_status="predraft",
    )

    assert league.league_id == "123.l.456"
    assert league.num_teams == 12


def test_player_model() -> None:
    player = Player(name="Patrick Mahomes", position="QB", team="KC")
    assert player.name == "Patrick Mahomes"
    assert player.position == "QB"
    assert player.team == "KC"


def test_player_accepts_any_position() -> None:
    player = Player(name="Shohei Ohtani", position="SP", team="LAD")
    assert player.position == "SP"


def test_ranked_player_model() -> None:
    player = Player(name="Josh Allen", position="QB", team="BUF")
    ranked = RankedPlayer(rank=2, player=player, notes="Dual threat")
    assert ranked.rank == 2
    assert ranked.player.name == "Josh Allen"
    assert ranked.notes == "Dual threat"


def test_ranked_player_default_notes() -> None:
    player = Player(name="Test", position="RB", team="NYG")
    ranked = RankedPlayer(rank=1, player=player)
    assert ranked.notes == ""


def test_draft_pick_model() -> None:
    pick = DraftPick(
        pick=1,
        round=1,
        team_key="423.l.123.t.1",
        player_key="423.p.100",
        player_name="Patrick Mahomes",
    )
    assert pick.pick == 1
    assert pick.round == 1
    assert pick.player_name == "Patrick Mahomes"


def test_draft_pick_default_player_name() -> None:
    pick = DraftPick(pick=1, round=1, team_key="t1", player_key="p1")
    assert pick.player_name == ""
