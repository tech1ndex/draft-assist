import json
from pathlib import Path

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from draft_assist.external.models import DraftPick, DraftResult, League, Player, PlayerStatus, Team
from draft_assist.settings import YahooSettings


class YahooFantasyClient:
    BASE_URL = "https://fantasysports.yahooapis.com/fantasy/v2"

    def __init__(self, settings: YahooSettings | None = None) -> None:
        self.settings = settings or YahooSettings()
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._load_tokens()

    def _load_tokens(self) -> None:
        token_path = Path(self.settings.token_file_path)
        if token_path.exists():
            try:
                with token_path.open() as f:
                    tokens = json.load(f)
                    self._access_token = tokens.get("access_token")
                    self._refresh_token = tokens.get("refresh_token")
                    logger.info("Loaded OAuth tokens from file")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load tokens: {e}")

    def _save_tokens(self) -> None:
        token_path = Path(self.settings.token_file_path)
        tokens = {
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
        }
        with token_path.open("w") as f:
            json.dump(tokens, f)
        logger.info("Saved OAuth tokens to file")

    def _get_headers(self) -> dict[str, str]:
        if not self._access_token:
            msg = "Not authenticated. Call authenticate() first."
            raise ValueError(msg)
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def get_auth_url(self) -> str:
        return (
            f"https://api.login.yahoo.com/oauth2/request_auth"
            f"?client_id={self.settings.client_id}"
            f"&redirect_uri={self.settings.redirect_uri}"
            f"&response_type=code"
            f"&scope=fspt-r"
        )

    def authenticate(self, auth_code: str) -> bool:
        token_url = "https://api.login.yahoo.com/oauth2/get_token"
        data = {
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
            "redirect_uri": self.settings.redirect_uri,
            "code": auth_code,
            "grant_type": "authorization_code",
        }

        try:
            response = requests.post(token_url, data=data, timeout=30)  # noqa: S113
            response.raise_for_status()
            tokens = response.json()
            self._access_token = tokens["access_token"]
            self._refresh_token = tokens["refresh_token"]
            self._save_tokens()
            logger.info("Successfully authenticated with Yahoo")
            return True
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def refresh_access_token(self) -> bool:

        if not self._refresh_token:
            logger.error("No refresh token available")
            return False

        token_url = "https://api.login.yahoo.com/oauth2/get_token"
        data = {
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
            "redirect_uri": self.settings.redirect_uri,
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = requests.post(token_url, data=data, timeout=30)  # noqa: S113
            response.raise_for_status()
            tokens = response.json()
            self._access_token = tokens["access_token"]
            self._refresh_token = tokens.get("refresh_token", self._refresh_token)
            self._save_tokens()
            logger.info("Successfully refreshed access token")
            return True
        except requests.RequestException as e:
            logger.error(f"Token refresh failed: {e}")
            return False

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _make_request(self, endpoint: str, method: str = "GET", data: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{endpoint}?format=json"
        headers = self._get_headers()

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                msg = f"Unsupported HTTP method: {method}"
                raise ValueError(msg)

            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 401:  # noqa: PLR2004
                logger.info("Token expired, attempting refresh...")
                if self.refresh_access_token():
                    return self._make_request(endpoint, method, data)
            raise

    def get_leagues(self, game_key: str = "nfl") -> list[League]:
        endpoint = f"/users;use_login=1/games;game_keys={game_key}/leagues"
        try:
            response = self._make_request(endpoint)
            leagues = []
            users = response.get("fantasy_content", {}).get("users", {})
            if users:
                user = users.get("0", {}).get("user", [])
                for item in user:
                    if isinstance(item, dict) and "games" in item:
                        games = item["games"]
                        for game_data in games.values():
                            if isinstance(game_data, dict) and "leagues" in game_data:
                                for league_data in game_data["leagues"].values():
                                    if isinstance(league_data, dict):
                                        league_info = league_data.get("league", [{}])[0]
                                        leagues.append(
                                            League(
                                                league_id=league_info.get("league_key", ""),
                                                name=league_info.get("name", ""),
                                                num_teams=int(league_info.get("num_teams", 0)),
                                                draft_status=league_info.get("draft_status", ""),
                                                season=int(league_info.get("season", 0)),
                                            )
                                        )
            return leagues
        except requests.RequestException as e:
            logger.error(f"Failed to get leagues: {e}")
            return []

    def get_league(self, league_key: str) -> League | None:
        endpoint = f"/league/{league_key}"
        try:
            response = self._make_request(endpoint)
            league_data = response.get("fantasy_content", {}).get("league", [{}])[0]
            return League(
                league_id=league_data.get("league_key", ""),
                name=league_data.get("name", ""),
                num_teams=int(league_data.get("num_teams", 0)),
                draft_status=league_data.get("draft_status", ""),
                current_week=int(league_data.get("current_week", 0)),
                season=int(league_data.get("season", 0)),
            )
        except requests.RequestException as e:
            logger.error(f"Failed to get league: {e}")
            return None

    def get_available_players(self, league_key: str, position: str | None = None) -> list[Player]:
        endpoint = f"/league/{league_key}/players;status=A"
        if position:
            endpoint += f";position={position}"

        try:
            response = self._make_request(endpoint)
            players = []
            players_data = response.get("fantasy_content", {}).get("league", [{}])
            if len(players_data) > 1:
                players_dict = players_data[1].get("players", {})
                for player_entry in players_dict.values():
                    if isinstance(player_entry, dict) and "player" in player_entry:
                        player_info = player_entry["player"][0]
                        name_data = next((p for p in player_info if isinstance(p, dict) and "name" in p), {})
                        players.append(
                            Player(
                                player_id=player_info[0].get("player_key", "") if player_info else "",
                                name=name_data.get("name", {}).get("full", ""),
                                team=next(
                                    (p.get("editorial_team_abbr", "") for p in player_info if isinstance(p, dict)),
                                    "",
                                ),
                                position=next(
                                    (p.get("display_position", "") for p in player_info if isinstance(p, dict)),
                                    "",
                                ),
                                status=PlayerStatus.AVAILABLE,
                            )
                        )
            return players
        except requests.RequestException as e:
            logger.error(f"Failed to get available players: {e}")
            return []

    def get_draft_results(self, league_key: str) -> list[DraftPick]:
        endpoint = f"/league/{league_key}/draftresults"
        try:
            response = self._make_request(endpoint)
            picks = []
            draft_data = response.get("fantasy_content", {}).get("league", [{}])
            if len(draft_data) > 1:
                draft_results = draft_data[1].get("draft_results", {})
                for pick_entry in draft_results.values():
                    if isinstance(pick_entry, dict) and "draft_result" in pick_entry:
                        pick_info = pick_entry["draft_result"]
                        picks.append(
                            DraftPick(
                                pick_number=int(pick_info.get("pick", 0)),
                                round_number=int(pick_info.get("round", 0)),
                                team_id=pick_info.get("team_key", ""),
                                player=Player(
                                    player_id=pick_info.get("player_key", ""),
                                    name="",  # Would need separate API call to get name
                                ),
                            )
                        )
            return picks
        except requests.RequestException as e:
            logger.error(f"Failed to get draft results: {e}")
            return []

    def make_draft_pick(self, league_key: str, player_key: str) -> DraftResult:
        # Note: Yahoo's API for making draft picks may require specific endpoints
        # This is a placeholder implementation
        endpoint = f"/league/{league_key}/players/{player_key}/draft"
        try:
            response = self._make_request(endpoint, method="POST")
            return DraftResult(
                success=True,
                message="Draft pick successful",
                player=Player(player_id=player_key, name=""),
            )
        except requests.RequestException as e:
            logger.error(f"Failed to make draft pick: {e}")
            return DraftResult(
                success=False,
                message=str(e),
            )

    def get_my_team(self, league_key: str, team_key: str) -> Team | None:
        """Get the authenticated user's team."""
        endpoint = f"/team/{team_key}/roster"
        try:
            response = self._make_request(endpoint)
            team_data = response.get("fantasy_content", {}).get("team", [{}])
            team_info = team_data[0] if team_data else {}

            roster = []
            if len(team_data) > 1:
                roster_data = team_data[1].get("roster", {}).get("0", {}).get("players", {})
                for player_entry in roster_data.values():
                    if isinstance(player_entry, dict) and "player" in player_entry:
                        player_info = player_entry["player"][0]
                        name_data = next((p for p in player_info if isinstance(p, dict) and "name" in p), {})
                        roster.append(
                            Player(
                                player_id=player_info[0].get("player_key", "") if player_info else "",
                                name=name_data.get("name", {}).get("full", ""),
                                position=next(
                                    (p.get("display_position", "") for p in player_info if isinstance(p, dict)),
                                    "",
                                ),
                            )
                        )

            return Team(
                team_id=team_info.get("team_key", ""),
                name=team_info.get("name", ""),
                roster=roster,
            )
        except requests.RequestException as e:
            logger.error(f"Failed to get team: {e}")
            return None
