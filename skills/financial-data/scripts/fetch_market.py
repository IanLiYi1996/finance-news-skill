#!/usr/bin/env python3
"""
fetch_market.py — 市场数据批量抓取脚本

用法：
  python3 fetch_market.py [--mode snapshot|detail|macro] [--symbols AAPL MSFT ...]

依赖：
  pip install yfinance akshare

模式：
  snapshot  — 全球主要指数 + 大宗商品 + 外汇快照（默认）
  detail    — 指定 symbol 的详细数据（用 --symbols 传入）
  macro     — 中美宏观经济指标
  crypto    — 加密货币行情（不需要 yfinance）
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime


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
    data = yf.download(all_symbols, period="2d", progress=False, auto_adjust=True)

    results = {}
    for category, symbols in SNAPSHOT_SYMBOLS.items():
        results[category] = {}
        for sym, name in symbols.items():
            try:
                closes = data["Close"][sym].dropna()
                if len(closes) < 2:
                    continue
                price = float(closes.iloc[-1])
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
    print(f"全球市场快照 — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'='*55}")
    for category, items in results.items():
        print(f"\n【{category}】")
        for name, d in items.items():
            arrow = "▲" if d["change_pct"] >= 0 else "▼"
            print(f"  {name:<18} {d['price']:>12,.3f}   {arrow}{abs(d['change_pct']):.2f}%")


# ── 详情模式 ──────────────────────────────────────────────

def detail_mode(symbols: list[str], output_json=False):
    yf = require("yfinance")
    results = {}
    for sym in symbols:
        ticker = yf.Ticker(sym)
        info   = ticker.info or {}
        hist   = ticker.history(period="5d")
        results[sym] = {
            "name":          info.get("longName") or info.get("shortName", sym),
            "currency":      info.get("currency", ""),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap":    info.get("marketCap"),
            "pe_ratio":      info.get("trailingPE"),
            "52w_high":      info.get("fiftyTwoWeekHigh"),
            "52w_low":       info.get("fiftyTwoWeekLow"),
            "volume":        info.get("volume"),
            "recent_closes": [round(float(p), 4) for p in hist["Close"].dropna().tolist()[-5:]],
        }

    if output_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for sym, d in results.items():
        print(f"\n[{sym}] {d['name']} ({d['currency']})")
        print(f"  当前价:   {d['current_price']}")
        print(f"  市值:     {d['market_cap']:,}" if d['market_cap'] else "  市值:     N/A")
        print(f"  P/E:      {d['pe_ratio']}")
        print(f"  52周高/低: {d['52w_high']} / {d['52w_low']}")
        print(f"  近5日收盘: {d['recent_closes']}")


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
    print(f"宏观经济指标 — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
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
    print(f"加密货币行情 — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
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
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出")
    args = parser.parse_args()

    if args.mode == "snapshot":
        snapshot_mode(args.json)
    elif args.mode == "detail":
        if not args.symbols:
            print("[ERROR] detail 模式需要 --symbols，例如：--symbols AAPL MSFT", file=sys.stderr)
            sys.exit(1)
        detail_mode(args.symbols, args.json)
    elif args.mode == "macro":
        macro_mode(args.json)
    elif args.mode == "crypto":
        crypto_mode(args.json)


if __name__ == "__main__":
    main()
