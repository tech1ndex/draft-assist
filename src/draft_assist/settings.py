from pydantic_settings import BaseSettings


class YahooSettings(BaseSettings):


    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "oob"
    token_file_path: str = "yahoo_token.json"


class DraftSettings(BaseSettings):


    rankings_file_path: str = "rankings.csv"
    league_id: str = ""
    team_id: str = ""
    auto_draft: bool = False
    draft_delay_seconds: float = 5.0
