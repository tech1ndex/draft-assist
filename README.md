# draft-assist

A CLI tool for Fantasy Sports draft preparation, powered by the Yahoo Fantasy Sports API. Written in Python.

## Features

- **Yahoo Integration**: OAuth2 authentication with the Yahoo Fantasy Sports API
- **League Discovery**: List your leagues across NFL, MLB, NBA, and other Yahoo Fantasy games
- **CLI Interface**: Command line interface powered by Typer

## Installation

### Prerequisites

- Python 3.13+
- [Poetry](https://python-poetry.org/)

### Setup

```bash
git clone https://github.com/tech1ndex/draft-assist.git
cd draft-assist

# Install dependencies
make install
```

## Usage

### 1. Create a Yahoo App

Go to [Yahoo Developer](https://developer.yahoo.com/apps/) and create an app with the **Fantasy Sports** API permission. Set the redirect URI to `https://localhost:8888`.

### 2. Set Environment Variables

```bash
export YAHOO_CLIENT_ID="your-client-id"
export YAHOO_CLIENT_SECRET="your-client-secret"
```

Or create a `.env` file in the project root:

```env
YAHOO_CLIENT_ID=your-client-id
YAHOO_CLIENT_SECRET=your-client-secret
```

### 3. Authenticate

```bash
draft-assist auth
```

This opens your browser for Yahoo OAuth. After authorizing, the CLI prints access/refresh tokens to export:

```bash
export YAHOO_ACCESS_TOKEN=...
export YAHOO_REFRESH_TOKEN=...
```

### 4. List Your Leagues

```bash
# NFL leagues (default)
draft-assist leagues

# MLB leagues
draft-assist leagues -g mlb

# NBA leagues
draft-assist leagues -g nba
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `YAHOO_CLIENT_ID` | Yahoo API client ID | |
| `YAHOO_CLIENT_SECRET` | Yahoo API client secret | |
| `YAHOO_ACCESS_TOKEN` | OAuth access token (from `auth` command) | |
| `YAHOO_REFRESH_TOKEN` | OAuth refresh token (from `auth` command) | |
| `YAHOO_REDIRECT_URI` | OAuth redirect URI | `https://localhost:8888` |

## Development

```bash
make install    # Install all dependencies (dev + test)
make lint       # Run mypy + ruff check + ruff format --check
make format     # Auto-fix ruff issues and format code
make test       # Run pytest with coverage
make all        # install + lint + test
make clean      # Remove caches and coverage files
```

Run a single test:

```bash
poetry run pytest tests/test_yahoo.py::test_authenticate_success -v
```

## Project Structure

```
draft-assist/
├── src/draft_assist/
│   ├── cli/                # Typer CLI commands
│   │   └── main.py
│   ├── external/           # External API clients
│   │   ├── models.py       # Pydantic models (League)
│   │   ├── oauth_server.py # OAuth callback server + SSL certs
│   │   └── yahoo.py        # Yahoo Fantasy API client
│   ├── logger/             # Logging setup
│   │   └── setup.py
│   └── settings.py         # Configuration (YahooSettings)
├── tests/
│   ├── test_cli.py
│   ├── test_models.py
│   ├── test_settings.py
│   └── test_yahoo.py
├── pyproject.toml
├── Makefile
└── README.md
```

## License

MIT
