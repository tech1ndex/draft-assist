import csv
import unicodedata
from pathlib import Path

from draft_assist.external.models import Player, RankedPlayer


def _normalize_name(name: str) -> str:
    """Lowercase and strip accents for consistent matching (e.g. Acuña → acuna)."""
    return (
        unicodedata.normalize("NFKD", name.lower())
        .encode("ascii", "ignore")
        .decode("ascii")
    )


class RankingsManager:
    def __init__(self, csv_path: Path) -> None:
        self._players = self._load_csv(csv_path)
        self._taken: set[str] = set()

    @staticmethod
    def _load_csv(csv_path: Path) -> list[RankedPlayer]:
        if not csv_path.exists():
            msg = f"Rankings file not found: {csv_path}"
            raise FileNotFoundError(msg)

        players: list[RankedPlayer] = []
        with csv_path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                player = Player(
                    name=row["name"],
                    position=row["position"],
                    team=row["team"],
                )
                ranked = RankedPlayer(
                    rank=int(row["rank"]),
                    player=player,
                    notes=row.get("notes", ""),
                )
                players.append(ranked)

        players.sort(key=lambda p: p.rank)
        return players

    def mark_taken(self, name: str) -> None:
        self._taken.add(_normalize_name(name))

    def get_best_available(
        self, position: str | None = None, limit: int = 10
    ) -> list[RankedPlayer]:
        players = [
            p
            for p in self._players
            if _normalize_name(p.player.name) not in self._taken
        ]
        if position is not None:
            players = [p for p in players if p.player.position == position]
        return players[:limit]

    def get_player(self, name: str) -> RankedPlayer | None:
        normalized = _normalize_name(name)
        for p in self._players:
            if _normalize_name(p.player.name) == normalized:
                return p
        return None
