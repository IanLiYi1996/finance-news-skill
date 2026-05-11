---
name: financial-data
description: "Fetch live financial news and market data — global/China stocks, indices, ETFs, FX, commodities, crypto, macro indicators (CPI/PMI/GDP/rates) — and assemble market reports or daily digests. Use this skill proactively whenever the user asks about markets, prices, quotes, tickers, news headlines, or economic data, even if they don't explicitly request a 'report'. Triggers on phrases like 'get market data', 'show me today's market', 'fetch news', 'how is the S&P / 纳斯达克 / 恒生 / 比特币 doing', '看看行情', '今日要闻', '抓取财经新闻', '生成市场报告', '财联社', 'macro data', 'CPI', 'PMI', 'Fed', 'earnings'. Also use when the user mentions a ticker symbol (AAPL, NVDA, 00700.HK, 600519.SS) and wants a price or snapshot."
---

# Financial Data Skill

Two scripts + two reference files. Covers news scraping and market-data fetching end-to-end.

## Quick pick: which tool?

| User wants… | Use |
|-------------|-----|
| 市场快照 / market snapshot / "how are markets doing" | `fetch_market.py` (default `snapshot` mode) |
| 具体股票价格 / ticker details / P/E / 52-week range | `fetch_market.py --mode detail --symbols …` |
| CPI / PMI / GDP / 利率 / macro indicators | `fetch_market.py --mode macro` |
| 加密货币 / crypto / BTC / ETH | `fetch_market.py --mode crypto` |
| 新闻 / headlines / 财经要闻 / 财联社 / WSJ / Bloomberg | `fetch_news.py` |
| 数据源/ticker 脚本没覆盖 | Read `references/market-data.md` or `references/news-sources.md` and copy the snippet |

If the user asks for something combining news + market (e.g. "make me a daily digest"), call both scripts and merge the output.

## Scripts

### `scripts/fetch_news.py` — financial news

```bash
# All sources (intl + cn + crypto + tech)
python3 scripts/fetch_news.py

# Chinese-only (财联社, 新浪财经, 澎湃, FT中文, 36氪)
python3 scripts/fetch_news.py --sources cn --limit 15

# International only, JSON for programmatic use
python3 scripts/fetch_news.py --sources intl --json

# Sources: all | intl | cn | crypto | tech
```

Only needs Python standard library + `curl`. No pip install required.

### `scripts/fetch_market.py` — market data

```bash
# Global snapshot (indices + commodities + FX + ETFs) — default
python3 scripts/fetch_market.py

# Specific tickers (yfinance)
python3 scripts/fetch_market.py --mode detail --symbols AAPL MSFT NVDA

# China + US macro indicators (akshare)
python3 scripts/fetch_market.py --mode macro

# Crypto prices + Fear & Greed index
python3 scripts/fetch_market.py --mode crypto

# JSON output
python3 scripts/fetch_market.py --mode snapshot --json
```

Dependencies (only install what you need):

```bash
pip install yfinance    # snapshot + detail modes
pip install akshare     # macro mode (China/US indicators)
# crypto mode uses CoinGecko public API — no install needed
```

If the user hasn't installed `yfinance` / `akshare`, run `pip install` for them before the first call in that mode.

## Reference files

Open these when the user asks for a source, ticker, or API the scripts don't already cover — they contain ready-to-copy code snippets.

- `references/news-sources.md` — every news feed URL (RSS/JSON/HTML), parsing templates, RSSHub routes, SearXNG + Tavily search configs
- `references/market-data.md` — full yfinance + akshare API examples, ticker symbol cheatsheets (indices / ETFs / FX / commodities / HK / A-shares), FRED and CoinGecko examples

## Common workflows

### Daily market digest
1. `fetch_market.py` → global snapshot
2. `fetch_news.py --sources intl` and `--sources cn` → headlines
3. Summarize top movers + 3–5 headlines per region
4. Deliver as markdown, Slack message, or email per user request

### Sector watch (e.g. semis, EVs)
```bash
python3 scripts/fetch_market.py --mode detail \
  --symbols NVDA AMD INTC SOXX 688981.SS 00981.HK
```

### Real-time flash news (财联社)
Script defaults to latest 30 items. Bump `rn=30` → `rn=100` in `fetch_news.py` if the user wants more.

### One-off: something the scripts don't cover
Don't try to improvise — open the relevant reference file, copy the snippet, adapt the ticker/URL. These files exist precisely for off-the-beaten-path requests.

## Output conventions

- Default (no `--json`): human-readable console output with ▲/▼ arrows and grouped sections. Good for pasting into chat.
- `--json`: structured data for downstream processing (charts, reports, Slack blocks).

When the user asks for a "report" or "digest", prefer the human-readable format, then add light markdown formatting (headings, tables). When piping into another tool, use `--json`.
