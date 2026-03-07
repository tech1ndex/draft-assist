from draft_assist.external.models import League


def test_league() -> None:
    league = League(
        league_id="123.l.456",
        name="Test League",
        num_teams=12,
        draft_status="predraft",
    )

    assert league.league_id == "123.l.456"
    assert league.num_teams == 12
