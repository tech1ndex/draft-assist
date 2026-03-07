from typing import Annotated

import typer

from draft_assist.external.yahoo import YahooFantasyClient
from draft_assist.logger.setup import setup_logger
from draft_assist.settings import get_yahoo_settings

app = typer.Typer(
    name="draft-assist",
    help="A Fantasy Sports Draft Assistant powered by your custom rankings.",
    add_completion=False,
)
logger = setup_logger()


@app.command(help="Authenticate with Yahoo Fantasy API and return tokens.")
def auth() -> None:
    settings = get_yahoo_settings()
    client = YahooFantasyClient(settings)

    logger.info("Opening browser for Yahoo authorization...")
    logger.info(
        "If you see a certificate warning, click Advanced → Proceed to localhost."
    )
    try:
        success = client.authenticate_via_browser()
    except RuntimeError as e:
        logger.exception(f"Browser auth failed: {e}")
        raise typer.Exit(code=1) from e

    if success:
        logger.info("Set these environment variables to persist your session:")
        typer.echo(f"export YAHOO_ACCESS_TOKEN={client.access_token}")
        typer.echo(f"export YAHOO_REFRESH_TOKEN={client.refresh_token}")


@app.command()
def leagues(
    game: Annotated[
        str, typer.Option("--game", "-g", help="Game key (e.g., nfl, nba, mlb)")
    ] = "nfl",
) -> None:
    client = YahooFantasyClient()

    if not client.is_authenticated:
        logger.error("Not authenticated. Run 'draft-assist auth' first.")
        raise typer.Exit(code=1)

    league_list = client.get_user_leagues(game)

    if league_list is None:
        raise typer.Exit(code=1)

    if not league_list:
        logger.info(f"No leagues found for game '{game}'.")
        return

    for league in league_list:
        typer.echo(
            f"{league.league_id}  {league.name}  ({league.num_teams} teams, {league.draft_status})"
        )


if __name__ == "__main__":
    app()
