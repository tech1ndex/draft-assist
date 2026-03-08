from pydantic import BaseModel


class Player(BaseModel):
    name: str
    position: str
    team: str


class RankedPlayer(BaseModel):
    rank: int
    player: Player
    notes: str = ""


class DraftPick(BaseModel):
    pick: int
    round: int
    team_key: str
    player_key: str
    player_name: str = ""


class League(BaseModel):
    league_id: str
    name: str
    num_teams: int = 0
    draft_status: str = ""
    current_week: int = 0
    season: int = 0
