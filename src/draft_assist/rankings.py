

import csv
from pathlib import Path

from loguru import logger

from draft_assist.external.models import RankedPlayer
from draft_assist.settings import DraftSettings


class RankingsManager:

    def __init__(self, settings: DraftSettings | None = None) -> None:
        """Initialize the rankings manager."""
        self.settings = settings or DraftSettings()
        self._rankings: list[RankedPlayer] = []

    def load_rankings(self, file_path: str | None = None) -> list[RankedPlayer]:
        path = Path(file_path or self.settings.rankings_file_path)

        if not path.exists():
            logger.warning(f"Rankings file not found: {path}")
            return []

        try:
            with path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self._rankings = []

                for row in reader:
                    try:
                        player = RankedPlayer(
                            rank=int(row.get("rank", 0)),
                            name=row.get("name", "").strip(),
                            position=row.get("position", "").strip().upper(),
                            team=row.get("team", "").strip().upper(),
                            notes=row.get("notes", "").strip(),
                        )
                        self._rankings.append(player)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid row: {row} - {e}")

                self._rankings.sort(key=lambda p: p.rank)
                logger.info(f"Loaded {len(self._rankings)} players from rankings file")
                return self._rankings

        except OSError as e:
            logger.error(f"Failed to read rankings file: {e}")
            return []

    def get_rankings(self) -> list[RankedPlayer]:
        return self._rankings

    def get_player_by_rank(self, rank: int) -> RankedPlayer | None:
        for player in self._rankings:
            if player.rank == rank:
                return player
        return None

    def get_player_by_name(self, name: str) -> RankedPlayer | None:
        name_lower = name.lower()
        for player in self._rankings:
            if player.name.lower() == name_lower:
                return player
        return None

    def get_players_by_position(self, position: str) -> list[RankedPlayer]:
        position_upper = position.upper()
        return [p for p in self._rankings if p.position == position_upper]

    def get_top_available(
        self,
        taken_names: set[str],
        count: int = 10,
        position: str | None = None,
    ) -> list[RankedPlayer]:
        taken_lower = {name.lower() for name in taken_names}
        available = []

        for player in self._rankings:
            if player.name.lower() in taken_lower:
                continue
            if position and player.position != position.upper():
                continue
            available.append(player)
            if len(available) >= count:
                break

        return available

    def get_best_available(self, taken_names: set[str], position: str | None = None) -> RankedPlayer | None:
        available = self.get_top_available(taken_names, count=1, position=position)
        return available[0] if available else None
