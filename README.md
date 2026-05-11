# financial-data

> An agent skill for fetching live financial news and market data — works with Claude Code, Cursor, Windsurf, Cline, Codex, and any other agent that supports [agent skills](https://skills.sh).

Give your coding agent the ability to pull real market snapshots, headlines, and macro data on demand. No API keys required for the basic flows.

## What it does

- 📈 **Market snapshots** — global indices, commodities, FX, ETFs (via `yfinance`)
- 🔍 **Ticker details** — price / P/E / 52-week range / recent closes for any symbol
- 🌏 **Macro indicators** — China & US CPI, PMI, GDP, rates (via `akshare`)
- ₿ **Crypto** — BTC / ETH / SOL / BNB / XRP + Fear & Greed index (CoinGecko, no key)
- 📰 **News feeds** — WSJ, FT, Bloomberg, Reuters, 财联社, 新浪财经, 澎湃, 36氪, CoinDesk, TechCrunch, and more

The skill bundles two ready-to-run Python scripts plus two reference cheatsheets the agent can consult when the user asks for a source or ticker the scripts don't cover out of the box.

## Install

With [`npx skills`](https://github.com/vercel-labs/skills) (recommended — works across Claude Code / Cursor / Windsurf / Cline / Codex / Gemini CLI / …):

```bash
# Into current project
npx skills add IanLiYi1996/finance-news-skill

# Into home (available globally)
npx skills add IanLiYi1996/finance-news-skill --global
```

The CLI auto-detects which agent(s) you use and drops `SKILL.md` + `scripts/` + `references/` into the right place (e.g. `.claude/skills/financial-data/` for Claude Code, `.cursor/skills/financial-data/` for Cursor).

### Manual install

If you don't want the CLI, clone this repo and copy the skill folder yourself:

```bash
git clone https://github.com/IanLiYi1996/finance-news-skill.git
cp -r finance-news-skill/skills/financial-data ~/.claude/skills/
# or your agent's equivalent skills directory
```

## Python dependencies

Install only what you need for the modes you'll use:

```bash
pip install yfinance    # for market snapshots + ticker details
pip install akshare     # for China/US macro indicators
# News scraping + crypto mode use only stdlib + curl
```

The agent will typically install these for you the first time you trigger a relevant mode.

## Usage

Once installed, just talk to your agent naturally:

- *"看看今天的市场"* → the skill triggers, runs `fetch_market.py`, summarizes movers
- *"Give me today's top financial headlines"* → runs `fetch_news.py`, groups by region
- *"How's NVDA looking?"* → runs `fetch_market.py --mode detail --symbols NVDA`
- *"生成一份市场日报发到 Slack"* → runs both scripts, assembles a digest

Or invoke the scripts directly:

```bash
# Global market snapshot
python3 skills/financial-data/scripts/fetch_market.py

# Chinese financial news, JSON
python3 skills/financial-data/scripts/fetch_news.py --sources cn --json

# China + US macro dashboard
python3 skills/financial-data/scripts/fetch_market.py --mode macro

# Crypto + Fear & Greed
python3 skills/financial-data/scripts/fetch_market.py --mode crypto
```

See `skills/financial-data/SKILL.md` for the full command reference.

## Project layout

```
financial-data/
├── README.md
├── LICENSE
└── skills/
    └── financial-data/
        ├── SKILL.md               # the skill manifest + instructions
        ├── scripts/
        │   ├── fetch_market.py    # yfinance / akshare / CoinGecko wrapper
        │   └── fetch_news.py      # RSS + JSON news aggregator
        └── references/
            ├── market-data.md     # ticker cheatsheets, API snippets
            └── news-sources.md    # feed URLs, parsing templates, RSSHub routes
```

This layout follows the `skills/<name>/` convention auto-discovered by `npx skills`, so the repo itself is the installable artifact — no registry, no manifest file needed.

## Supported agents

Anything that reads `SKILL.md`-style agent skills, including:

- [Claude Code](https://www.anthropic.com/claude-code) (`.claude/skills/`)
- [Cursor](https://cursor.com) (`.cursor/skills/` or `.agents/skills/`)
- [Windsurf](https://codeium.com/windsurf)
- [Cline](https://github.com/cline/cline)
- [OpenAI Codex CLI](https://github.com/openai/codex)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- Goose, Qwen CLI, Kilo, Kiro, Amp, Copilot CLI, Continue, Aider, and others supported by `npx skills`

## Adding your own sources

The reference files (`references/news-sources.md`, `references/market-data.md`) are designed to be extended. Add a new feed URL or ticker, and the agent will find it next time it consults the reference for an off-the-beaten-path request.

## License

MIT — see [LICENSE](LICENSE).
