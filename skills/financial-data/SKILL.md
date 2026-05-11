---
name: financial-data
description: "Fetch live financial news and market data — global/China stocks, indices, ETFs, FX, commodities, crypto, macro indicators (CPI/PMI/GDP/rates) — plus per-ticker deep data (financials, dividends, analyst ratings, related news, technicals, A-share fund flow). Use proactively whenever the user asks about markets, prices, quotes, tickers, news headlines, economic data, earnings, dividends, analyst targets, or fund flow. Triggers on phrases like 'get market data', 'show me today's market', 'fetch news', 'how is the S&P / 纳斯达克 / 恒生 / 比特币 doing', '看看行情', '今日要闻', '抓取财经新闻', '生成市场报告', '财联社', 'macro data', 'CPI', 'PMI', 'Fed', 'earnings', '股息率', '分析师目标价', '主力资金流向', '研报'. Also use when the user mentions a ticker (AAPL, NVDA, 00700.HK, 600519.SS) and wants price, fundamentals, news, or a full profile."
---

# Financial Data Skill

Two scripts + two reference files. Covers news scraping and market-data fetching end-to-end.

## Quick pick: which tool?

| User wants… | Use |
|-------------|-----|
| 市场快照 / market snapshot / "how are markets doing" | `fetch_market.py` (default `snapshot` mode) |
| 具体股票价格 / ticker details / P/E / 52-week range | `fetch_market.py --mode detail --symbols …` |
| 财务报表 / 分红 / 分析师目标价 / 相关新闻 / 技术指标 / A股资金流 | 同上 + `--include …`（见下文） |
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

### `--include` bundles (detail mode)

Use these when the user wants more than just price and market cap. Bundles combine cleanly — pass a comma-separated list.

| Bundle | Contents | Needs |
|--------|----------|-------|
| `analyst` | Rating + number of analysts + mean / low / high target price | yfinance |
| `dividends` | Dividend yield + payout ratio + last 5 dividend payments | yfinance |
| `financials` | Quarterly revenue / net income / operating cash flow (last 2 quarters) | yfinance |
| `news` | Last 5 ticker-specific news stories (title + URL) | yfinance |
| `technicals` | MA5/20/50 + RSI(14) + 20-day avg volume | yfinance |
| `flow` | Latest 主力/超大单/大单/中单/小单 net flow + recent notices | akshare; auto-skips non-A-share |
| `all` | Everything above | both |

Pick the smallest set that answers the user's question. Loading `all` on 10 symbols is slow — only do that when they explicitly want a deep dive.

### `scripts/fetch_market.py` — market data

```bash
# Global snapshot (indices + commodities + FX + ETFs) — default
python3 scripts/fetch_market.py

# Specific tickers (yfinance)
python3 scripts/fetch_market.py --mode detail --symbols AAPL MSFT NVDA

# Deep per-ticker profile (pick the bundles you need)
python3 scripts/fetch_market.py --mode detail --symbols AAPL \
  --include analyst,technicals,news,dividends,financials

# A-share fund flow (auto-detected by .SS/.SZ/.BJ suffix)
python3 scripts/fetch_market.py --mode detail --symbols 600519.SS \
  --include flow

# Everything at once
python3 scripts/fetch_market.py --mode detail --symbols NVDA --include all

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

### Deep dive on a single name
"Tell me everything about NVDA" →
```bash
python3 scripts/fetch_market.py --mode detail --symbols NVDA --include all
```
The agent should then pick out the 3–5 most relevant facts (target price vs current, recent earnings trend, top news headline, technical posture) rather than dumping the raw output.

### A-share with fund flow
"看看贵州茅台的主力资金" →
```bash
python3 scripts/fetch_market.py --mode detail --symbols 600519.SS --include flow
```

### Real-time flash news (财联社)
Script defaults to latest 30 items. Bump `rn=30` → `rn=100` in `fetch_news.py` if the user wants more.

### One-off: something the scripts don't cover
Don't try to improvise — open the relevant reference file, copy the snippet, adapt the ticker/URL. These files exist precisely for off-the-beaten-path requests.

## Output conventions

- Default (no `--json`): human-readable console output with ▲/▼ arrows and grouped sections. Good for pasting into chat.
- `--json`: structured data for downstream processing (charts, reports, Slack blocks).

When the user asks for a "report" or "digest", prefer the human-readable format, then add light markdown formatting (headings, tables). When piping into another tool, use `--json`.
