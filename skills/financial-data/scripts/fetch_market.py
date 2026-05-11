#!/usr/bin/env python3
"""
fetch_market.py — 市场数据批量抓取脚本

用法：
  python3 fetch_market.py [--mode snapshot|detail|macro|crypto] [--symbols AAPL MSFT ...]
                          [--include financials,dividends,analyst,news,technicals,flow]

依赖：
  pip install yfinance akshare

模式：
  snapshot  — 全球主要指数 + 大宗商品 + 外汇快照（默认）
  detail    — 指定 symbol 的详细数据（--symbols 必填，--include 可选补充）
  macro     — 中美宏观经济指标
  crypto    — 加密货币行情（无需 yfinance）

--include bundles（仅 detail 模式）：
  financials  — 季度营收/利润/经营现金流
  dividends   — 分红历史 + 股息率
  analyst     — 分析师评级 + 目标价
  news        — 个股相关新闻
  technicals  — MA/RSI/成交量技术指标
  flow        — A股主力资金流向 + 公告（自动按 .SS/.SZ/.BJ 判定）
  all         — 全部加载
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone


def require(pkg):
    """尝试导入，失败则提示安装。"""
    try:
        return __import__(pkg)
    except ImportError:
        print(f"[ERROR] 缺少依赖: pip install {pkg}", file=sys.stderr)
        sys.exit(1)


# ── 快照模式 ──────────────────────────────────────────────

SNAPSHOT_SYMBOLS = {
    "指数": {
        "^GSPC": "S&P 500",
        "^IXIC": "纳斯达克",
        "^DJI":  "道琼斯",
        "^VIX":  "VIX",
        "^N225": "日经225",
        "^HSI":  "恒生指数",
        "000001.SS": "上证综指",
        "^FTSE": "富时100",
    },
    "大宗商品": {
        "GC=F": "黄金",
        "CL=F": "WTI原油",
        "BZ=F": "布伦特原油",
        "SI=F": "白银",
        "HG=F": "铜",
        "NG=F": "天然气",
    },
    "外汇": {
        "DX-Y.NYB": "美元指数",
        "EURUSD=X": "欧元/美元",
        "USDJPY=X": "美元/日元",
        "USDCNH=X": "美元/离岸人民币",
        "GBPUSD=X": "英镑/美元",
    },
    "ETF": {
        "SPY":  "标普500 ETF",
        "QQQ":  "纳斯达克 ETF",
        "GLD":  "黄金 ETF",
        "TLT":  "20年美债 ETF",
        "SOXX": "费城半导体 ETF",
    },
}


def snapshot_mode(output_json=False):
    yf = require("yfinance")
    all_symbols = [s for group in SNAPSHOT_SYMBOLS.values() for s in group]
    # Use 7 calendar days rather than 2: weekends + holidays can leave futures
    # and some FX pairs with only 1 bar in a 2-day window, which drops them
    # from the output entirely. 7d guarantees ≥2 trading bars across all
    # market schedules.
    data = yf.download(all_symbols, period="7d", progress=False, auto_adjust=True)

    results = {}
    for category, symbols in SNAPSHOT_SYMBOLS.items():
        results[category] = {}
        for sym, name in symbols.items():
            try:
                closes = data["Close"][sym].dropna()
                if len(closes) == 0:
                    continue
                price = float(closes.iloc[-1])
                # Some instruments (futures/FX) may only have 1 bar over a
                # holiday weekend. Show price, mark change as unavailable
                # rather than dropping the row entirely.
                if len(closes) < 2:
                    results[category][name] = {
                        "symbol": sym,
                        "price":  round(price, 4),
                        "change_pct": None,
                    }
                    continue
                prev  = float(closes.iloc[-2])
                chg   = (price - prev) / prev * 100
                results[category][name] = {
                    "symbol": sym,
                    "price":  round(price, 4),
                    "change_pct": round(chg, 2),
                }
            except Exception:
                pass

    if output_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    print(f"\n{'='*55}")
    print(f"全球市场快照 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'='*55}")
    for category, items in results.items():
        print(f"\n【{category}】")
        for name, d in items.items():
            chg = d["change_pct"]
            if chg is None:
                print(f"  {name:<18} {d['price']:>12,.3f}   (no prior close)")
            else:
                arrow = "▲" if chg >= 0 else "▼"
                print(f"  {name:<18} {d['price']:>12,.3f}   {arrow}{abs(chg):.2f}%")


# ── 详情模式 ──────────────────────────────────────────────

# 可用的 --include bundles（仅当用户明确要求时才加载，避免默认输出过长）
DETAIL_BUNDLES = {
    "financials": "营收 / 净利润 / 经营现金流（近 2 期）",
    "dividends":  "分红历史 + 股息率",
    "analyst":    "分析师评级 + 平均目标价",
    "news":       "个股相关新闻（近 5 条）",
    "technicals": "5/20/50 日均线 + RSI(14) + 平均成交量",
    "flow":       "A 股主力资金流向（仅 .SS/.SZ/.BJ）",
}


def _is_a_share(sym: str) -> bool:
    return sym.upper().endswith((".SS", ".SZ", ".BJ"))


def _a_share_code(sym: str) -> str:
    """AAPL -> AAPL；600519.SS -> 600519"""
    return sym.split(".", 1)[0]


def _bundle_financials(ticker) -> dict:
    """季度 income statement + cash flow 的最近两期，加上 TTM 指标。"""
    out = {}
    info = ticker.info or {}
    # TTM / YoY 增速（info 字段，"免费" — 不用再拉 statement）
    ttm = {}
    for label, key in [
        ("revenue_ttm",       "totalRevenue"),
        ("gross_margin",      "grossMargins"),
        ("operating_margin",  "operatingMargins"),
        ("earnings_growth_yoy","earningsGrowth"),
        ("revenue_growth_yoy","revenueGrowth"),
        ("total_cash",        "totalCash"),
        ("total_debt",        "totalDebt"),
    ]:
        if info.get(key) is not None:
            ttm[label] = info[key]
    if ttm:
        out["ttm"] = ttm

    try:
        inc = ticker.quarterly_income_stmt
        if inc is not None and not inc.empty:
            out["revenue"] = {str(c.date()): _num(inc.loc["Total Revenue", c])
                              for c in inc.columns[:2] if "Total Revenue" in inc.index}
            out["net_income"] = {str(c.date()): _num(inc.loc["Net Income", c])
                                 for c in inc.columns[:2] if "Net Income" in inc.index}
    except Exception as e:
        out["income_error"] = str(e)
    try:
        cf = ticker.quarterly_cashflow
        if cf is not None and not cf.empty and "Operating Cash Flow" in cf.index:
            out["operating_cash_flow"] = {str(c.date()): _num(cf.loc["Operating Cash Flow", c])
                                          for c in cf.columns[:2]}
    except Exception as e:
        out["cashflow_error"] = str(e)
    return out


def _bundle_dividends(ticker, info: dict) -> dict:
    out = {"dividend_yield": info.get("dividendYield"),
           "payout_ratio":   info.get("payoutRatio")}
    try:
        divs = ticker.dividends
        if divs is not None and len(divs) > 0:
            out["recent_dividends"] = {str(d.date()): round(float(v), 4)
                                       for d, v in divs.tail(5).items()}
    except Exception as e:
        out["error"] = str(e)
    return out


def _bundle_analyst(info: dict) -> dict:
    return {
        "recommendation":     info.get("recommendationKey"),
        "analysts":           info.get("numberOfAnalystOpinions"),
        "target_mean":        info.get("targetMeanPrice"),
        "target_low":         info.get("targetLowPrice"),
        "target_high":        info.get("targetHighPrice"),
    }


def _bundle_news(ticker, limit: int = 5) -> list:
    try:
        raw = ticker.news or []
    except Exception as e:
        return [{"error": str(e)}]
    items = []
    for n in raw[:limit]:
        content = n.get("content", n)  # newer yfinance wraps under "content"
        title = content.get("title") or n.get("title", "")
        link  = (content.get("canonicalUrl") or {}).get("url") or n.get("link", "")
        pub   = content.get("pubDate") or n.get("providerPublishTime", "")
        if title:
            items.append({"title": title, "url": link, "published": str(pub)})
    return items


def _bundle_technicals(ticker) -> dict:
    """用 1 年历史算技术指标 — 涵盖 MA200、MACD、Bollinger。"""
    try:
        hist = ticker.history(period="1y")
        closes = hist["Close"].dropna()
        volumes = hist["Volume"].dropna()
        if len(closes) < 20:
            return {"error": "not enough data"}

        def _ma(n):
            return round(float(closes.tail(n).mean()), 4) if len(closes) >= n else None

        # Wilder's RSI(14) — use EWMA of gains/losses, the standard.
        diff = closes.diff().dropna()
        gains = diff.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
        losses = (-diff.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
        last_gain, last_loss = float(gains.iloc[-1]), float(losses.iloc[-1])
        rsi = 100.0 if last_loss == 0 else 100 - 100 / (1 + last_gain / last_loss)

        # MACD (12/26/9)
        macd_out = None
        if len(closes) >= 26:
            ema12 = closes.ewm(span=12, adjust=False).mean()
            ema26 = closes.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            macd_out = {
                "macd":      round(float(macd.iloc[-1]), 4),
                "signal":    round(float(signal.iloc[-1]), 4),
                "histogram": round(float((macd - signal).iloc[-1]), 4),
            }

        # Bollinger Bands (20, 2σ)
        bb = None
        if len(closes) >= 20:
            window = closes.tail(20)
            mid = window.mean()
            sd  = window.std()
            bb = {
                "upper":  round(float(mid + 2 * sd), 4),
                "middle": round(float(mid), 4),
                "lower":  round(float(mid - 2 * sd), 4),
            }

        return {
            "last_close":      round(float(closes.iloc[-1]), 4),
            "ma5":  _ma(5),
            "ma20": _ma(20),
            "ma50": _ma(50),
            "ma200": _ma(200),
            "rsi14":           round(float(rsi), 2),
            "macd":            macd_out,
            "bollinger_20_2": bb,
            "avg_volume_20d":  int(volumes.tail(20).mean()),
        }
    except Exception as e:
        return {"error": str(e)}


def _bundle_flow(sym: str) -> dict:
    """A 股主力资金流向 + 近 5 条公告 — 需 akshare。"""
    if not _is_a_share(sym):
        return {"skipped": "not an A-share symbol (need .SS/.SZ/.BJ suffix)"}
    try:
        ak = __import__("akshare")
    except ImportError:
        return {"error": "pip install akshare"}

    code = _a_share_code(sym)
    # akshare 的市场代码需要 sh/sz/bj 小写
    market = {"SS": "sh", "SZ": "sz", "BJ": "bj"}[sym.rsplit(".", 1)[1].upper()]
    out = {}
    try:
        df = ak.stock_individual_fund_flow(stock=code, market=market)
        if df is not None and not df.empty:
            last = df.iloc[-1]
            out["fund_flow_latest"] = {str(k): str(v) for k, v in last.items()}
    except Exception as e:
        out["fund_flow_error"] = str(e)
    try:
        # 个股公告（近 5 条）
        news = ak.stock_news_em(symbol=code)
        if news is not None and not news.empty:
            out["recent_notices"] = [{"title": r["新闻标题"], "time": str(r["发布时间"])}
                                     for _, r in news.head(5).iterrows()]
    except Exception as e:
        out["notices_error"] = str(e)
    return out


def _num(v):
    """Convert pandas scalar to plain int/None for JSON output."""
    try:
        import math
        if v is None:
            return None
        f = float(v)
        return None if math.isnan(f) else int(f) if abs(f) > 1 else round(f, 4)
    except Exception:
        return None


def detail_mode(symbols: list[str], include: set[str], output_json=False):
    yf = require("yfinance")
    results = {}
    for sym in symbols:
        ticker = yf.Ticker(sym)
        info   = ticker.info or {}
        hist   = ticker.history(period="5d")
        entry = {
            "name":          info.get("longName") or info.get("shortName", sym),
            "currency":      info.get("currency", ""),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap":    info.get("marketCap"),
            "pe_ratio":      info.get("trailingPE"),
            "forward_pe":    info.get("forwardPE"),
            "peg_ratio":     info.get("trailingPegRatio") or info.get("pegRatio"),
            "profit_margin": info.get("profitMargins"),
            "roe":           info.get("returnOnEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "free_cash_flow": info.get("freeCashflow"),
            "beta":          info.get("beta"),
            "52w_high":      info.get("fiftyTwoWeekHigh"),
            "52w_low":       info.get("fiftyTwoWeekLow"),
            "volume":        info.get("volume"),
            "recent_closes": [round(float(p), 4) for p in hist["Close"].dropna().tolist()[-5:]],
        }
        if "financials" in include: entry["financials"] = _bundle_financials(ticker)
        if "dividends"  in include: entry["dividends"]  = _bundle_dividends(ticker, info)
        if "analyst"    in include: entry["analyst"]    = _bundle_analyst(info)
        if "news"       in include: entry["news"]       = _bundle_news(ticker)
        if "technicals" in include: entry["technicals"] = _bundle_technicals(ticker)
        if "flow"       in include: entry["flow"]       = _bundle_flow(sym)
        results[sym] = entry

    if output_json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
        return

    def _pct(x):
        return f"{x*100:.2f}%" if isinstance(x, (int, float)) else "N/A"

    for sym, d in results.items():
        print(f"\n[{sym}] {d['name']} ({d['currency']})")
        print(f"  当前价:    {d['current_price']}")
        print(f"  市值:      {d['market_cap']:,}" if d['market_cap'] else "  市值:      N/A")
        print(f"  P/E:       trailing {d['pe_ratio']} | forward {d['forward_pe']} | PEG {d['peg_ratio']}")
        print(f"  利润率:    净利率 {_pct(d['profit_margin'])} | ROE {_pct(d['roe'])} | 营收增速 {_pct(d['revenue_growth'])}")
        if d.get("free_cash_flow"):
            print(f"  自由现金流: {d['free_cash_flow']:,}")
        print(f"  Beta:      {d['beta']}")
        print(f"  52周高/低: {d['52w_high']} / {d['52w_low']}")
        print(f"  近5日收盘: {d['recent_closes']}")

        if "analyst" in d:
            a = d["analyst"]
            print(f"\n  ── 分析师 ──")
            print(f"  评级:      {a['recommendation']} ({a['analysts']} 位分析师)")
            print(f"  目标价:    均 {a['target_mean']} | 区间 {a['target_low']} – {a['target_high']}")

        if "dividends" in d:
            dv = d["dividends"]
            print(f"\n  ── 分红 ──")
            print(f"  股息率:    {dv['dividend_yield']}")
            print(f"  派息率:    {dv['payout_ratio']}")
            if dv.get("recent_dividends"):
                print(f"  近5次:     {dv['recent_dividends']}")

        if "financials" in d:
            f = d["financials"]
            print(f"\n  ── 财务 ──")
            if "ttm" in f:
                ttm = f["ttm"]
                if "revenue_ttm" in ttm: print(f"  TTM 营收:   {ttm['revenue_ttm']:,}")
                print(f"  毛利率:     {_pct(ttm.get('gross_margin'))}  |  营业利润率: {_pct(ttm.get('operating_margin'))}")
                print(f"  营收 YoY:   {_pct(ttm.get('revenue_growth_yoy'))}  |  盈利 YoY: {_pct(ttm.get('earnings_growth_yoy'))}")
                if "total_cash" in ttm and "total_debt" in ttm:
                    net = ttm["total_cash"] - ttm["total_debt"]
                    print(f"  现金/负债:  {ttm['total_cash']:,} / {ttm['total_debt']:,}  净现金 {net:,}")
            for k in ("revenue", "net_income", "operating_cash_flow"):
                if k in f:
                    print(f"  {k:20s} {f[k]}")

        if "technicals" in d:
            t = d["technicals"]
            if "error" in t:
                print(f"\n  ── 技术指标 ──  ERROR: {t['error']}")
            else:
                print(f"\n  ── 技术指标 ──")
                print(f"  MA5/20/50/200: {t['ma5']} / {t['ma20']} / {t['ma50']} / {t['ma200']}")
                rsi = t["rsi14"]
                tag = "超买 (>70)" if rsi > 70 else "超卖 (<30)" if rsi < 30 else "中性"
                print(f"  RSI(14):   {rsi}  ({tag})")
                if t.get("macd"):
                    m = t["macd"]
                    trend = "多头" if m["histogram"] > 0 else "空头"
                    print(f"  MACD:      {m['macd']} / signal {m['signal']} / hist {m['histogram']}  ({trend})")
                if t.get("bollinger_20_2"):
                    b = t["bollinger_20_2"]
                    print(f"  Bollinger: {b['lower']} – {b['middle']} – {b['upper']}")
                print(f"  20日均量:  {t['avg_volume_20d']:,}")

        if "flow" in d:
            fl = d["flow"]
            print(f"\n  ── A股资金流向 / 公告 ──")
            if "skipped" in fl:
                print(f"  跳过: {fl['skipped']}")
            else:
                if "fund_flow_latest" in fl:
                    print(f"  最新资金流: {fl['fund_flow_latest']}")
                if "recent_notices" in fl:
                    print(f"  近期公告:")
                    for n in fl["recent_notices"]:
                        print(f"    - [{n['time']}] {n['title']}")

        if "news" in d:
            print(f"\n  ── 相关新闻 ──")
            for n in d["news"]:
                if "error" in n:
                    print(f"  ERROR: {n['error']}")
                else:
                    print(f"  • {n['title']}")
                    if n.get("url"): print(f"    {n['url']}")


# ── 宏观模式 ──────────────────────────────────────────────

def macro_mode(output_json=False):
    ak = require("akshare")
    results = {}

    macro_tasks = [
        ("中国CPI",  ak.macro_china_cpi),
        ("中国PPI",  ak.macro_china_ppi),
        ("中国PMI",  ak.macro_china_pmi),
        ("中国GDP",  ak.macro_china_gdp),
        ("美国CPI",  ak.macro_usa_cpi),
        ("美国PMI",  ak.macro_usa_ism_pmi),
        ("美国GDP",  ak.macro_usa_gdp),
        ("美国失业率", ak.macro_usa_unemployment_rate),
    ]

    for name, fn in macro_tasks:
        try:
            df = fn()
            last = df.iloc[-1].to_dict()
            results[name] = {k: str(v) for k, v in last.items()}
        except Exception as e:
            results[name] = {"error": str(e)}

    if output_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    print(f"\n{'='*55}")
    print(f"宏观经济指标 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'='*55}")
    for name, d in results.items():
        if "error" in d:
            print(f"\n[{name}] ERROR: {d['error']}")
        else:
            print(f"\n[{name}]")
            for k, v in d.items():
                print(f"  {k}: {v}")


# ── 加密货币模式 ──────────────────────────────────────────

def crypto_mode(output_json=False):
    raw = subprocess.run(
        ["curl", "-s",
         "https://api.coingecko.com/api/v3/simple/price"
         "?ids=bitcoin,ethereum,solana,bnb,xrp"
         "&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"],
        capture_output=True, text=True
    ).stdout
    fng_raw = subprocess.run(
        ["curl", "-s", "https://api.alternative.me/fng/?limit=1"],
        capture_output=True, text=True
    ).stdout

    try:
        prices = json.loads(raw)
    except Exception:
        prices = {}
    try:
        fng = json.loads(fng_raw)["data"][0]
    except Exception:
        fng = {}

    if output_json:
        print(json.dumps({"prices": prices, "fear_greed": fng}, ensure_ascii=False, indent=2))
        return

    print(f"\n{'='*55}")
    print(f"加密货币行情 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'='*55}")
    names = {"bitcoin": "比特币", "ethereum": "以太坊",
             "solana": "Solana", "bnb": "BNB", "xrp": "XRP"}
    for coin_id, d in prices.items():
        name = names.get(coin_id, coin_id)
        chg  = d.get("usd_24h_change", 0)
        arrow = "▲" if chg >= 0 else "▼"
        print(f"  {name:<10} ${d['usd']:>12,.2f}  {arrow}{abs(chg):.2f}%")
    if fng:
        print(f"\n  恐贪指数: {fng.get('value')} — {fng.get('value_classification')}")


# ── 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="市场数据抓取工具")
    parser.add_argument("--mode", default="snapshot",
                        choices=["snapshot", "detail", "macro", "crypto"],
                        help="运行模式（默认 snapshot）")
    parser.add_argument("--symbols", nargs="+", default=[],
                        help="detail 模式下指定 symbol，如 AAPL MSFT")
    parser.add_argument("--include", default="",
                        help=("detail 模式额外字段，逗号分隔；可选："
                              + ", ".join(DETAIL_BUNDLES.keys())
                              + "。或用 'all' 加载全部。"))
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出")
    args = parser.parse_args()

    if args.mode == "snapshot":
        snapshot_mode(args.json)
    elif args.mode == "detail":
        if not args.symbols:
            print("[ERROR] detail 模式需要 --symbols，例如：--symbols AAPL MSFT", file=sys.stderr)
            sys.exit(1)
        if args.include.strip().lower() == "all":
            include = set(DETAIL_BUNDLES.keys())
        else:
            include = {x.strip() for x in args.include.split(",") if x.strip()}
            unknown = include - set(DETAIL_BUNDLES)
            if unknown:
                print(f"[ERROR] 未知 --include 选项: {unknown}。可选: {list(DETAIL_BUNDLES)}",
                      file=sys.stderr)
                sys.exit(1)
        detail_mode(args.symbols, include, args.json)
    elif args.mode == "macro":
        macro_mode(args.json)
    elif args.mode == "crypto":
        crypto_mode(args.json)


if __name__ == "__main__":
    main()
