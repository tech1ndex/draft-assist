from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PlayerStatus(str, Enum):
    AVAILABLE = "available"
    TAKEN = "taken"
    INJURED = "injured"


class Position(str, Enum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"
    FLEX = "FLEX"
    BENCH = "BN"


class Player(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    player_id: str = Field(alias="player_id")
    name: str
    team: str = ""
    position: str = ""
    status: PlayerStatus = PlayerStatus.AVAILABLE
    bye_week: int | None = None
    percent_owned: float = 0.0


class RankedPlayer(BaseModel):
    rank: int
    name: str
    position: str = ""
    team: str = ""
    notes: str = ""


class DraftPick(BaseModel):
    pick_number: int
    round_number: int
    team_id: str
    player: Player | None = None
    timestamp: datetime | None = None


class League(BaseModel):
    league_id: str
    name: str
    num_teams: int = 0
    draft_status: str = ""
    current_week: int = 0
    season: int = 0


class Team(BaseModel):
    team_id: str
    name: str
    manager: str = ""
    roster: list[Player] = Field(default_factory=list)


class DraftResult(BaseModel):
    success: bool
    message: str
    player: Player | None = None
    pick_number: int | None = None
