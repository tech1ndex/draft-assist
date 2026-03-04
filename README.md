# draft-assist

A simple Python tool to assist with Fantasy Sports Drafting, written with love in Python.

## Features

- **Custom Rankings**: Import your player rankings from a CSV file
- **Yahoo Integration**: Connect to Yahoo Fantasy Sports API for live draft data
- **Best Available**: Quickly see the best available players based on your rankings
- **Position Filtering**: Filter suggestions by position
- **CLI Interface**: Easy-to-use command line interface powered by Typer

## Installation

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/)

### Setup

```bash
# Clone the repository
git clone https://github.com/tech1ndex/draft-assist.git
cd draft-assist

# Install dependencies
poetry install

# Or use make
make install
```

## Usage

### Prepare Your Rankings

Create a CSV file with your player rankings:

```csv
rank,name,position,team,notes
1,Patrick Mahomes,QB,KC,Elite QB
2,Travis Kelce,TE,KC,Top TE
3,Tyreek Hill,WR,MIA,Speed demon
...
```

See `rankings.example.csv` for a complete example.

### CLI Commands

#### View Your Rankings

```bash
# Show top 20 players
draft-assist rankings --file rankings.csv

# Filter by position
draft-assist rankings --file rankings.csv --position WR

# Show top N
draft-assist rankings --file rankings.csv --top 50
```

#### Best Available

```bash
# Show best available players
draft-assist available --file rankings.csv

# With a list of taken players
draft-assist available --file rankings.csv --taken taken.txt

# Filter by position
draft-assist available --file rankings.csv --position RB --top 5
```

#### Yahoo Fantasy Integration

```bash
# Authenticate with Yahoo
export YAHOO_CLIENT_ID="your-client-id"
export YAHOO_CLIENT_SECRET="your-client-secret"
draft-assist auth

# List your leagues
draft-assist leagues

# Start draft assistant
draft-assist draft --league "nfl.l.123456"
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `YAHOO_CLIENT_ID` | Yahoo API client ID |
| `YAHOO_CLIENT_SECRET` | Yahoo API client secret |
| `YAHOO_LEAGUE_ID` | Default league ID |
| `RANKINGS_FILE` | Path to rankings CSV file |

## Development

```bash
# Install all dependencies including dev
make install

# Run linting
make lint

# Run tests
make test

# Format code
make format

# Run all checks
make all
```

## Project Structure

```
draft-assist/
├── src/draft_assist/
│   ├── cli/              # Typer CLI commands
│   │   ├── __init__.py
│   │   └── main.py
│   ├── external/         # External API clients
│   │   ├── __init__.py
│   │   ├── models.py     # Pydantic models
│   │   └── yahoo.py      # Yahoo Fantasy client
│   ├── logger/           # Logging setup
│   │   ├── __init__.py
│   │   └── setup.py
│   ├── __init__.py
│   ├── rankings.py       # Rankings management
│   └── settings.py       # Configuration
├── tests/
│   ├── test_models.py
│   └── test_rankings.py
├── pyproject.toml
├── Makefile
└── README.md
```

## License

MIT
