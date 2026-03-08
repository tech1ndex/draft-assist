import typer

from draft_assist.cli.draft import app as draft_app
from draft_assist.cli.league import app as league_app
from draft_assist.external.yahoo import YahooFantasyClient
from draft_assist.logger.setup import setup_logger
from draft_assist.settings import get_yahoo_settings

app = typer.Typer(
    name="draft-assist",
    help="A Fantasy Sports Draft Assistant powered by your custom rankings.",
    add_completion=False,
)
app.add_typer(league_app, name="league")
app.add_typer(draft_app, name="draft")


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


if __name__ == "__main__":
    app()
