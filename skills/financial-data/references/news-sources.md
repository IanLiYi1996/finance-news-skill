# Financial News Sources

## 解析代码模板

### RSS XML 通用解析
```python
import xml.etree.ElementTree as ET, subprocess
data = subprocess.run(['curl','-sL','<URL>','--max-time','8'], capture_output=True, text=True).stdout
root = ET.fromstring(data)
for item in root.findall('.//item')[:10]:
    print(item.find('title').text)
    print(item.find('link').text)
    print((item.find('description').text or '')[:120])
```

### 财联社 JSON 解析
```python
import json, subprocess
data = subprocess.run(['curl','-s','https://www.cls.cn/nodeapi/updateTelegraphList?app=CailianpressWeb&os=web&sv=8.4.6&rn=20'], capture_output=True, text=True).stdout
for item in json.loads(data)['data']['roll_data']:
    print(item.get('title') or item.get('content','')[:100])
```

### 新浪财经 JSON 解析
```python
import json, subprocess
data = subprocess.run(['curl','-s','https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=10&page=1'], capture_output=True, text=True).stdout
for item in json.loads(data)['result']['data']:
    print(item['title'], item.get('url',''))
```

---

## 国际英文财经

| 名称 | URL | 状态 |
|------|-----|------|
| WSJ Markets | `https://feeds.a.dj.com/rss/RSSMarketsMain.xml` | ✅ |
| WSJ World | `https://feeds.a.dj.com/rss/RSSWorldNews.xml` | ✅ |
| FT Home | `https://www.ft.com/rss/home` | ✅ |
| Economist Finance | `https://www.economist.com/finance-and-economics/rss.xml` | ✅ |
| Bloomberg Markets | `https://feeds.bloomberg.com/markets/news.rss` | RSS |
| CNBC Top News | `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114` | RSS |
| MarketWatch | `https://feeds.marketwatch.com/marketwatch/topstories/` | RSS |
| Benzinga | `https://www.benzinga.com/feed` | ✅ |
| Motley Fool | `https://www.fool.com/feeds/index.aspx` | ✅ |
| SeekingAlpha | `https://seekingalpha.com/market_currents.xml` | Atom |
| ZeroHedge | `https://feeds.feedburner.com/zerohedge/feed` | RSS |
| BBC Business | `https://feeds.bbci.co.uk/news/business/rss.xml` | RSS |
| NYT Business | `https://rss.nytimes.com/services/xml/rss/nyt/Business.xml` | RSS |
| Investing.com | `https://www.investing.com/rss/news.rss` | RSS |

## 央行 & 政策

| 名称 | URL | 说明 |
|------|-----|------|
| 美联储 Press | `https://www.federalreserve.gov/feeds/press_all.xml` | FOMC/政策 ✅ |
| 美联储 Speeches | `https://www.federalreserve.gov/feeds/speeches.xml` | 官员讲话 |
| ECB Press | `https://www.ecb.europa.eu/rss/press.html` | 欧央行 |

## 加密货币

| 名称 | URL |
|------|-----|
| CoinDesk | `https://www.coindesk.com/arc/outboundfeeds/rss/` |
| Cointelegraph | `https://cointelegraph.com/rss` |
| Decrypt | `https://decrypt.co/feed` |

## 科技 & AI

| 名称 | URL |
|------|-----|
| TechCrunch | `https://techcrunch.com/feed/` |
| The Verge | `https://www.theverge.com/rss/index.xml` |
| Hacker News Best | `https://hnrss.org/best` |
| ArsTechnica | `https://feeds.arstechnica.com/arstechnica/index` |

---

## 中文财经

| 名称 | URL | 格式 |
|------|-----|------|
| 财联社电报 | `https://www.cls.cn/nodeapi/updateTelegraphList?app=CailianpressWeb&os=web&sv=8.4.6&rn=30` | JSON |
| 新浪财经滚动 | `https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=10&page=1` | JSON ✅ |
| 澎湃新闻 | `https://feedx.net/rss/thepaper.xml` | RSS ✅ |
| 36氪 | `https://36kr.com/feed` | RSS |
| FeedX 华尔街日报中文 | `https://feedx.net/rss/wsj.xml` | RSS |
| FeedX 金融时报中文 | `https://feedx.net/rss/ftchinese.xml` | RSS |

## 网页抓取源（用 web_fetch）

| 名称 | URL |
|------|-----|
| Reuters 全球市场 | `https://www.reuters.com/markets/` |
| Reuters 美股 | `https://www.reuters.com/markets/us/` |
| Reuters 亚太 | `https://www.reuters.com/markets/asia/` |
| 华尔街见闻 | `https://wallstreetcn.com/news/global` |
| 金十数据 | `https://www.jin10.com/` |

---

## RSSHub 路由（需自建或用公共实例）

公共实例：`https://rsshub.rssforever.com`（备选：`https://rsshub.pseudoyu.com`）

自建（推荐）：
```bash
docker run -d --name rsshub -p 1200:1200 diygod/rsshub
```

| 路由 | 说明 |
|------|------|
| `/jin10/flash` | 金十数据实时快讯 ✅ |
| `/wallstreetcn/news/global` | 华尔街见闻全球要闻 ✅ |
| `/cls/telegraph` | 财联社电报 ✅ |
| `/xueqiu/hots` | 雪球热帖 |
| `/eastmoney/report/strategyreport` | 东方财富策略研报 |
| `/gelonghui/live` | 格隆汇港美股快讯 |
| `/21caijing/channel/finance` | 21世纪经济深度财经 |
| `/yicai/brief` | 第一财经要闻 |
| `/telegram/channel/{channelname}` | Telegram频道（如 GlobalFinance_ZH） |

```python
import subprocess, xml.etree.ElementTree as ET
RSSHUB = "https://rsshub.rssforever.com"
data = subprocess.run(['curl','-sL',f'{RSSHUB}/jin10/flash','--max-time','8'], capture_output=True, text=True).stdout
root = ET.fromstring(data)
for item in root.findall('.//item')[:10]:
    print(item.find('title').text)
```

---

## 本地 SearXNG（自建搜索引擎，首选）
```bash
curl -s "http://localhost:8888/search?q=搜索内容&format=json&pageno=1" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d.get('results',[])[:5]:
    print(f\"{r['title']}\n  {r['url']}\n  {r.get('content','')[:120]}\n\")
"
```
- 容器名: searxng，端口: 8888，聚合 Google/Bing/DuckDuckGo

## Tavily（备用搜索 API）

Get a free key at https://tavily.com, export it as `TAVILY_API_KEY`:

```bash
curl -s -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"$TAVILY_API_KEY\",\"query\":\"搜索内容\",\"max_results\":5,\"search_depth\":\"advanced\",\"include_answer\":true}"
```
