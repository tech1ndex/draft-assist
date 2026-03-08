from typing import Annotated

import typer

from draft_assist.external.yahoo import YahooFantasyClient
from draft_assist.logger.setup import setup_logger
from draft_assist.settings import get_yahoo_settings, save_env_setting

app = typer.Typer(help="Interact with a league that you have access to.")
logger = setup_logger()


def _get_authenticated_client() -> YahooFantasyClient:
    settings = get_yahoo_settings()
    client = YahooFantasyClient(settings)
    if not client.is_authenticated:
        logger.error("Not authenticated. Run 'draft-assist auth' first.")
        raise typer.Exit(code=1)
    return client


@app.command(help="Show a list of leagues that you have access to.")
def show(
    game: Annotated[
        str, typer.Option("--game", "-g", help="Game key (e.g., nfl, nba, mlb)")
    ] = "nfl",
) -> None:
    client = _get_authenticated_client()

    league_list = client.get_user_leagues(game)

    if league_list is None:
        raise typer.Exit(code=1)

    if not league_list:
        logger.info(f"No leagues found for game '{game}'.")
        return

    for lg in league_list:
        typer.echo(
            f"League ID: {lg.league_id} \n"
            f"League Name: {lg.name} \n"
            f"({lg.num_teams} teams, {lg.draft_status})"
        )


@app.command(help="Set the active league for draft commands.")
def use(
    league_id: Annotated[
        str,
        typer.Argument(help="League ID (from the first column of 'league list')"),
    ],
) -> None:
    client = _get_authenticated_client()

    league = client.get_league(league_id)
    if league is None:
        logger.error(f"League '{league_id}' not found or could not be retrieved.")
        raise typer.Exit(code=1)

    save_env_setting("DRAFT_LEAGUE_ID", league_id)
    logger.info(f"Active league set to: {league.name} ({league_id})")
