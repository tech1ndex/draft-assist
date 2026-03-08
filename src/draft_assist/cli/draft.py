import time
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger as loguru_logger
from rich.console import Console
from rich.live import Live
from rich.table import Table

from draft_assist.external.models import RankedPlayer
from draft_assist.external.yahoo import YahooFantasyClient
from draft_assist.logger.setup import setup_logger
from draft_assist.rankings import RankingsManager
from draft_assist.settings import get_draft_settings, get_yahoo_settings

app = typer.Typer(help="Interact with a draft.")
logger = setup_logger()
console = Console()


def _get_authenticated_client() -> YahooFantasyClient:
    settings = get_yahoo_settings()
    client = YahooFantasyClient(settings)
    if not client.is_authenticated:
        logger.error("Not authenticated. Run 'draft-assist auth' first.")
        raise typer.Exit(code=1)
    return client


def _load_manager() -> RankingsManager:
    settings = get_draft_settings()
    csv_path = Path(settings.rankings_path)
    try:
        return RankingsManager(csv_path)
    except FileNotFoundError:
        logger.exception(f"Rankings file not found: {csv_path}")
        raise typer.Exit(code=1) from None


def _render_table(players: list[RankedPlayer], title: str) -> None:
    table = Table(title=title)
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Pos", style="magenta")
    table.add_column("Team", style="green")
    table.add_column("Notes", style="dim")

    for p in players:
        table.add_row(
            str(p.rank), p.player.name, p.player.position, p.player.team, p.notes
        )

    console.print(table)


@app.command(help="Get a list of drafts in your league.")
def show(
    league_id: Annotated[
        str | None,
        typer.Argument(help="League ID (from the first column of 'league list')"),
    ] = None,
) -> None:
    client = _get_authenticated_client()
    effective_id = league_id or get_draft_settings().league_id
    if not effective_id:
        logger.error(
            "No league ID provided. Pass it as an argument or run 'draft-assist league set <id>'."
        )
        raise typer.Exit(code=1)
    draft = client.get_drafts(effective_id)
    console.print(draft)


@app.command(help="Display all ranked players.")
def rankings(
    position: Annotated[
        str | None, typer.Option(help="Filter by position (e.g. QB, SP, C)")
    ] = None,
    limit: Annotated[int, typer.Option(help="Max players to display")] = 20,
) -> None:
    manager = _load_manager()
    pos = position.upper() if position else None
    players = manager.get_best_available(position=pos, limit=limit)
    title = "Rankings"
    if pos:
        title += f" — {pos}"
    _render_table(players, title)


@app.command(help="Show best available players.")
def available(
    position: Annotated[
        str | None, typer.Option(help="Filter by position (e.g. QB, SP, C)")
    ] = None,
    limit: Annotated[int, typer.Option(help="Max players to display")] = 10,
) -> None:
    manager = _load_manager()
    pos = position.upper() if position else None
    players = manager.get_best_available(position=pos, limit=limit)
    title = "Best Available"
    if pos:
        title += f" — {pos}"
    _render_table(players, title)


def _build_live_table(
    players: list[RankedPlayer], pick_count: int, position: str | None = None
) -> Table:
    title = f"Best Available ({pick_count} picks made)"
    if position:
        title += f" — {position}"
    table = Table(title=title)
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Pos", style="magenta")
    table.add_column("Team", style="green")
    table.add_column("Notes", style="dim")
    for p in players:
        table.add_row(
            str(p.rank), p.player.name, p.player.position, p.player.team, p.notes
        )
    return table


@app.command(
    help="Live draft tracker — polls Yahoo for picks and updates best available."
)
def live(
    position: Annotated[
        str | None, typer.Option(help="Filter by position (e.g. QB, SP, C)")
    ] = None,
    limit: Annotated[int, typer.Option(help="Max players to display")] = 15,
    interval: Annotated[int, typer.Option(help="Polling interval in seconds")] = 5,
) -> None:
    client = _get_authenticated_client()
    manager = _load_manager()
    settings = get_draft_settings()
    league_id = settings.league_id
    if not league_id:
        logger.error("No league ID set. Run 'draft-assist league use <id>' first.")
        raise typer.Exit(code=1)

    pos = position.upper() if position else None
    console.print("Starting live draft tracker. Press Ctrl+C to exit.")

    loguru_logger.disable("draft_assist")
    seen_picks: set[int] = set()
    try:
        players = manager.get_best_available(position=pos, limit=limit)
        with Live(
            _build_live_table(players, 0, pos), console=console, refresh_per_second=1
        ) as live_display:
            while True:
                picks = client.get_draft_results(league_id)
                new_picks = [p for p in picks if p.pick not in seen_picks]
                for pick in new_picks:
                    seen_picks.add(pick.pick)
                    if pick.player_name:
                        manager.mark_taken(pick.player_name)
                if new_picks:
                    players = manager.get_best_available(position=pos, limit=limit)
                    live_display.update(
                        _build_live_table(players, len(seen_picks), pos)
                    )
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        loguru_logger.enable("draft_assist")
        console.print("Draft tracking stopped.")
