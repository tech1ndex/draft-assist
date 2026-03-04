from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from draft_assist.external.models import RankedPlayer
from draft_assist.external.yahoo import YahooFantasyClient
from draft_assist.logger.setup import setup_logger
from draft_assist.rankings import RankingsManager
from draft_assist.settings import DraftSettings, YahooSettings

app = typer.Typer(
    name="draft-assist",
    help="A Fantasy Sports Draft Assistant powered by your custom rankings.",
    add_completion=False,
)
console = Console()
logger = setup_logger()


@app.callback()
def main() -> None:
    """Draft Assist - Your Fantasy Sports Draft Companion."""


@app.command()
def auth(
    client_id: Annotated[str, typer.Option("--client-id", "-c", help="Yahoo API client ID", envvar="YAHOO_CLIENT_ID")],
    client_secret: Annotated[
        str, typer.Option("--client-secret", "-s", help="Yahoo API client secret", envvar="YAHOO_CLIENT_SECRET")
    ],
) -> None:
    settings = YahooSettings(client_id=client_id, client_secret=client_secret)
    client = YahooFantasyClient(settings)

    auth_url = client.get_auth_url()
    console.print("\n[bold blue]Yahoo OAuth Authentication[/bold blue]\n")
    console.print("1. Open this URL in your browser:")
    console.print(f"   [link={auth_url}]{auth_url}[/link]\n")
    console.print("2. Authorize the application")
    console.print("3. Copy the authorization code and paste it below\n")

    auth_code = typer.prompt("Enter the authorization code")

    if client.authenticate(auth_code):
        console.print("\n[green]Successfully authenticated![/green]")
        console.print(f"Tokens saved to: {settings.token_file_path}")
    else:
        console.print("\n[red]Authentication failed. Please try again.[/red]")
        raise typer.Exit(code=1)


@app.command()
def leagues(
    client_id: Annotated[
        str, typer.Option("--client-id", "-c", help="Yahoo API client ID", envvar="YAHOO_CLIENT_ID")
    ] = "",
    client_secret: Annotated[
        str, typer.Option("--client-secret", "-s", help="Yahoo API client secret", envvar="YAHOO_CLIENT_SECRET")
    ] = "",
    game: Annotated[str, typer.Option("--game", "-g", help="Game key (e.g., nfl, nba, mlb)")] = "nfl",
) -> None:
    settings = YahooSettings(client_id=client_id, client_secret=client_secret)
    client = YahooFantasyClient(settings)

    if not client.is_authenticated:
        console.print("[red]Not authenticated. Run 'draft-assist auth' first.[/red]")
        raise typer.Exit(code=1)

    league_list = client.get_leagues(game)

    if not league_list:
        console.print("[yellow]No leagues found.[/yellow]")
        return

    table = Table(title="Your Fantasy Leagues")
    table.add_column("League ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Teams", justify="right")
    table.add_column("Draft Status", style="yellow")
    table.add_column("Season", justify="right")

    for league in league_list:
        table.add_row(
            league.league_id,
            league.name,
            str(league.num_teams),
            league.draft_status,
            str(league.season),
        )

    console.print(table)


@app.command()
def rankings(
    file: Annotated[
        Path, typer.Option("--file", "-f", help="Path to rankings CSV file", envvar="RANKINGS_FILE")
    ] = Path("rankings.csv"),
    position: Annotated[str | None, typer.Option("--position", "-p", help="Filter by position")] = None,
    top: Annotated[int, typer.Option("--top", "-t", help="Show top N players")] = 20,
) -> None:
    """Display your player rankings."""
    settings = DraftSettings(rankings_file_path=str(file))
    manager = RankingsManager(settings)

    player_list = manager.load_rankings()

    if not player_list:
        console.print(f"[red]No rankings found in {file}[/red]")
        console.print("\nExpected CSV format:")
        console.print("  rank,name,position,team,notes")
        console.print("  1,Patrick Mahomes,QB,KC,Elite QB")
        raise typer.Exit(code=1)

    if position:
        player_list = manager.get_players_by_position(position)

    player_list = player_list[:top]

    _display_rankings_table(player_list, f"Player Rankings (Top {len(player_list)})")


def _display_rankings_table(players: list[RankedPlayer], title: str) -> None:
    table = Table(title=title)
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Pos", style="yellow")
    table.add_column("Team", style="blue")
    table.add_column("Notes", style="dim")

    for player in players:
        table.add_row(
            str(player.rank),
            player.name,
            player.position,
            player.team,
            player.notes,
        )

    console.print(table)


@app.command()
def available(
    file: Annotated[
        Path, typer.Option("--file", "-f", help="Path to rankings CSV file", envvar="RANKINGS_FILE")
    ] = Path("rankings.csv"),
    taken: Annotated[
        Path | None, typer.Option("--taken", "-t", help="Path to file listing taken players (one per line)")
    ] = None,
    position: Annotated[str | None, typer.Option("--position", "-p", help="Filter by position")] = None,
    top: Annotated[int, typer.Option("--top", "-n", help="Show top N available")] = 10,
) -> None:
    settings = DraftSettings(rankings_file_path=str(file))
    manager = RankingsManager(settings)

    if not manager.load_rankings():
        console.print(f"[red]No rankings found in {file}[/red]")
        raise typer.Exit(code=1)

    taken_names: set[str] = set()
    if taken and taken.exists():
        with taken.open() as f:
            taken_names = {line.strip() for line in f if line.strip()}
        console.print(f"[dim]Loaded {len(taken_names)} taken players[/dim]\n")

    available_players = manager.get_top_available(taken_names, count=top, position=position)

    if not available_players:
        console.print("[yellow]No available players found matching criteria.[/yellow]")
        return

    title = "Best Available"
    if position:
        title += f" ({position.upper()})"

    _display_rankings_table(available_players, title)


@app.command()
def draft(
    league_id: Annotated[str, typer.Option("--league", "-l", help="Yahoo league ID", envvar="YAHOO_LEAGUE_ID")],
    file: Annotated[
        Path, typer.Option("--file", "-f", help="Path to rankings CSV file", envvar="RANKINGS_FILE")
    ] = Path("rankings.csv"),
    client_id: Annotated[
        str, typer.Option("--client-id", "-c", help="Yahoo API client ID", envvar="YAHOO_CLIENT_ID")
    ] = "",
    client_secret: Annotated[
        str, typer.Option("--client-secret", "-s", help="Yahoo API client secret", envvar="YAHOO_CLIENT_SECRET")
    ] = "",
    auto: Annotated[bool, typer.Option("--auto", "-a", help="Enable auto-draft mode")] = False,
) -> None:
    yahoo_settings = YahooSettings(client_id=client_id, client_secret=client_secret)
    draft_settings = DraftSettings(rankings_file_path=str(file), league_id=league_id, auto_draft=auto)

    client = YahooFantasyClient(yahoo_settings)
    manager = RankingsManager(draft_settings)

    if not client.is_authenticated:
        console.print("[red]Not authenticated. Run 'draft-assist auth' first.[/red]")
        raise typer.Exit(code=1)

    if not manager.load_rankings():
        console.print(f"[red]No rankings found in {file}[/red]")
        raise typer.Exit(code=1)

    league = client.get_league(league_id)
    if not league:
        console.print(f"[red]Could not find league: {league_id}[/red]")
        raise typer.Exit(code=1)

    console.print(f"\n[bold green]Draft Assistant - {league.name}[/bold green]")
    console.print(f"League ID: {league.league_id}")
    console.print(f"Draft Status: {league.draft_status}\n")

    if league.draft_status != "postdraft":
        draft_results = client.get_draft_results(league_id)
        taken_ids = {pick.player.player_id for pick in draft_results if pick.player}
        console.print(f"[dim]Picks made: {len(draft_results)}[/dim]\n")

        best = manager.get_top_available(set(), count=5)
        if best:
            console.print("[bold]Suggested picks (from your rankings):[/bold]")
            _display_rankings_table(best, "Best Available")

        if auto:
            console.print("\n[yellow]Auto-draft mode is enabled but not yet implemented.[/yellow]")
            console.print("This would automatically pick the best available player when it's your turn.")
    else:
        console.print("[yellow]Draft has already completed.[/yellow]")


@app.command()
def version() -> None:
    from draft_assist import __version__
    console.print(f"draft-assist version {__version__}")


if __name__ == "__main__":
    app()
