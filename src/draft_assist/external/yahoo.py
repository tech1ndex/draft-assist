import webbrowser
from urllib.parse import urlencode

import requests
from loguru import logger
from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from draft_assist.external.models import League
from draft_assist.external.oauth_server import wait_for_auth_code
from draft_assist.settings import YahooSettings, get_yahoo_settings


def _iter_league_dicts(game_val: dict) -> list[dict]:
    game_entry = game_val.get("game", [])
    if len(game_entry) < 2:  # noqa: PLR2004
        return []
    league_entries = game_entry[1].get("leagues", {})
    if not isinstance(league_entries, dict):
        return []
    return [
        lv.get("league", [{}])[0]
        for lv in league_entries.values()
        if isinstance(lv, dict)
    ]


def _build_league(data: dict) -> League:
    return League(
        league_id=data.get("league_key", ""),
        name=data.get("name", ""),
        num_teams=int(data.get("num_teams", 0)),
        draft_status=data.get("draft_status", ""),
        current_week=int(data.get("current_week", 0)),
        season=int(data.get("season", 0)),
    )


class YahooFantasyClient:
    def __init__(self, settings: YahooSettings | None = None) -> None:
        self._settings = settings or get_yahoo_settings()
        self._access_token: str | None = self._settings.access_token or None
        self._refresh_token: str | None = self._settings.refresh_token or None

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    def _get_headers(self) -> dict[str, str]:
        if not self._access_token:
            msg = "Not authenticated. Call authenticate() first."
            raise ValueError(msg)
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def get_auth_url(self) -> str:
        params = {
            "client_id": self._settings.client_id,
            "redirect_uri": self._settings.redirect_uri,
            "response_type": "code",
            "scope": "fspt-r",
        }
        return f"{self._settings.oauth_base_url}/request_auth?{urlencode(params)}"

    def _exchange_token(self, grant_data: dict[str, str]) -> bool:
        data = {
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
            "redirect_uri": self._settings.redirect_uri,
            **grant_data,
        }
        try:
            response = requests.post(self._settings.token_url, data=data, timeout=30)
            response.raise_for_status()
            tokens = response.json()
            self._access_token = tokens["access_token"]
            self._refresh_token = tokens.get("refresh_token", self._refresh_token)
        except requests.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            return False
        else:
            return True

    def authenticate(self, auth_code: str) -> bool:
        result = self._exchange_token(
            {"code": auth_code, "grant_type": "authorization_code"}
        )
        if result:
            logger.info("Successfully authenticated with Yahoo")
        return result

    def refresh_access_token(self) -> bool:
        if not self._refresh_token:
            logger.error("No refresh token available")
            return False

        result = self._exchange_token(
            {"refresh_token": self._refresh_token, "grant_type": "refresh_token"}
        )
        if result:
            logger.info("Successfully refreshed access token")
            logger.warning(
                "Token refreshed. Update your environment:\n"
                f"  export YAHOO_ACCESS_TOKEN={self._access_token}\n"
                f"  export YAHOO_REFRESH_TOKEN={self._refresh_token}"
            )
        return result

    def authenticate_via_browser(self, port: int = 8888) -> bool:
        auth_url = self.get_auth_url()
        logger.info(f"Opening browser for authorization: {auth_url}")
        webbrowser.open(auth_url)
        auth_code = self._wait_for_auth_code(port=port)
        return self.authenticate(auth_code)

    def authenticate_with_refresh_token(self, refresh_token: str) -> bool:
        self._refresh_token = refresh_token
        return self.refresh_access_token()

    @staticmethod
    def _wait_for_auth_code(port: int = 8888, timeout: int = 120) -> str:
        return wait_for_auth_code(port=port, timeout=timeout)

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    @staticmethod
    def _is_retryable(exc: BaseException) -> bool:
        if isinstance(exc, requests.ConnectionError | requests.Timeout):
            return True
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            return exc.response.status_code >= 500  # noqa: PLR2004
        return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_is_retryable),
    )
    def _make_request(
        self, endpoint: str, method: str = "GET", data: dict | None = None
    ) -> dict:
        url = f"{self._settings.api_url}{endpoint}?format=json"
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
            if (
                e.response is not None
                and e.response.status_code == 401  # noqa: PLR2004
            ):
                logger.info("Token expired, attempting refresh...")
                if self.refresh_access_token():
                    return self._make_request(endpoint, method, data)
            raise

    def get_user_leagues(self, game_key: str) -> list[League] | None:
        endpoint = f"/users;use_login=1/games;game_keys={game_key}/leagues"
        try:
            response = self._make_request(endpoint)
        except (requests.RequestException, RetryError) as e:
            logger.error(f"Failed to get leagues: {e}")
            return None
        return self._parse_leagues(response)

    @staticmethod
    def _parse_leagues(response: dict) -> list[League] | None:
        users = (
            response.get("fantasy_content", {})
            .get("users", {})
            .get("0", {})
            .get("user", [])
        )
        if len(users) < 2:  # noqa: PLR2004
            return []
        game_data = users[1].get("games", {})
        leagues: list[League] = []
        for val in game_data.values():
            if not isinstance(val, dict):
                continue
            leagues.extend(_build_league(info) for info in _iter_league_dicts(val))
        return leagues

    def get_league(self, league_key: str) -> League | None:
        endpoint = f"/league/{league_key}"
        try:
            response = self._make_request(endpoint)
            league_data = response.get("fantasy_content", {}).get("league", [{}])[0]
            return _build_league(league_data)
        except (requests.RequestException, RetryError) as e:
            logger.error(f"Failed to get league: {e}")
            return None
