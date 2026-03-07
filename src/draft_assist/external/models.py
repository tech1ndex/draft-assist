from pydantic import BaseModel


class League(BaseModel):
    league_id: str
    name: str
    num_teams: int = 0
    draft_status: str = ""
    current_week: int = 0
    season: int = 0
