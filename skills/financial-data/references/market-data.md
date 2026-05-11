# Market Data Reference

## yfinance — 美股/全球市场

### 安装
```bash
pip install yfinance
```

### 单只股票
```python
import yfinance as yf
ticker = yf.Ticker("AAPL")
info = ticker.info          # 公司基本信息
hist = ticker.history(period="1mo")   # 历史行情
financials = ticker.financials        # 财务报表
```

### 批量下载
```python
import yfinance as yf
data = yf.download(["AAPL","GOOGL","MSFT"], period="5d")
# 或指定日期
data = yf.download(["SPY","QQQ"], start="2024-01-01", end="2024-12-31")
```

### 常用 Symbol 速查

**主要指数**
| Symbol | 名称 |
|--------|------|
| `^GSPC` | S&P 500 |
| `^DJI` | 道琼斯 |
| `^IXIC` | 纳斯达克 |
| `^VIX` | VIX 恐慌指数 |
| `^FTSE` | 富时100 |
| `^N225` | 日经225 |
| `^HSI` | 恒生指数 |
| `000001.SS` | 上证综指 |
| `399001.SZ` | 深证成指 |
| `^KS11` | 韩国KOSPI |
| `^TWII` | 台湾加权 |

**主要 ETF**
| Symbol | 名称 |
|--------|------|
| `SPY` | 标普500 ETF |
| `QQQ` | 纳斯达克ETF |
| `GLD` | 黄金ETF |
| `TLT` | 20年美债ETF |
| `USO` | 原油ETF |
| `EEM` | 新兴市场ETF |
| `FXI` | 中国ETF |
| `SOXX` | 费城半导体ETF |
| `XLE` | 能源板块ETF |
| `XLK` | 科技板块ETF |

**外汇**
| Symbol | 名称 |
|--------|------|
| `EURUSD=X` | 欧元/美元 |
| `USDJPY=X` | 美元/日元 |
| `USDCNH=X` | 美元/离岸人民币 |
| `GBPUSD=X` | 英镑/美元 |
| `DX-Y.NYB` | 美元指数 |

**大宗商品期货**
| Symbol | 名称 |
|--------|------|
| `GC=F` | 黄金 |
| `SI=F` | 白银 |
| `CL=F` | WTI 原油 |
| `BZ=F` | 布伦特原油 |
| `HG=F` | 铜 |
| `NG=F` | 天然气 |

**加密货币**
| Symbol | 名称 |
|--------|------|
| `BTC-USD` | 比特币 |
| `ETH-USD` | 以太坊 |

---

## akshare — A股/港股/宏观数据

### 安装
```bash
pip install akshare
```

### A股行情
```python
import akshare as ak
df = ak.stock_zh_a_spot_em()          # A股全市场实时行情
hist = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq"                        # 前复权
)
```

### 港股
```python
hk = ak.stock_hk_spot_em()            # 港股实时行情
hk_hist = ak.stock_hk_hist(symbol="00700", period="daily", start_date="20240101")
```

### 期货
```python
futures = ak.futures_main_sina()       # 国内主力合约行情
```

### 宏观经济 — 中国
```python
cpi = ak.macro_china_cpi()            # CPI
ppi = ak.macro_china_ppi()            # PPI（生产者价格指数）
pmi = ak.macro_china_pmi()            # PMI
gdp = ak.macro_china_gdp()            # GDP
m2 = ak.macro_china_money_supply()    # 货币供应量（M0/M1/M2）
lpr = ak.macro_china_lpr()            # LPR 贷款市场报价利率
```

### 宏观经济 — 美国
```python
us_cpi = ak.macro_usa_cpi()           # CPI
us_ppi = ak.macro_usa_ppi()           # PPI
us_gdp = ak.macro_usa_gdp()           # GDP
us_unemployment = ak.macro_usa_unemployment_rate()  # 失业率
us_ism = ak.macro_usa_ism_pmi()       # ISM制造业PMI
us_nonfarm = ak.macro_usa_non_farm()  # 非农就业
```

### 板块资金流
```python
sector_flow = ak.stock_sector_fund_flow_rank(
    indicator="今日",
    sector_type="行业资金流"
)
```

### 外汇即期报价
```python
fx_rate = ak.fx_spot_quote()
```

---

## 免费 API

### CoinGecko（加密货币，无需 Key）
```python
import subprocess, json
price = subprocess.run(
    ['curl','-s','https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true'],
    capture_output=True, text=True
).stdout
print(json.loads(price))

# 全球市场概览
global_data = subprocess.run(
    ['curl','-s','https://api.coingecko.com/api/v3/global'],
    capture_output=True, text=True
).stdout
```

### Fear & Greed Index（Crypto，无需 Key）
```python
import subprocess, json
fng = subprocess.run(
    ['curl','-s','https://api.alternative.me/fng/?limit=1'],
    capture_output=True, text=True
).stdout
data = json.loads(fng)['data'][0]
print(f"恐贪指数: {data['value']} ({data['value_classification']})")
```

### FRED（美联储经济数据，需免费注册 Key）
- 注册：https://fred.stlouisfed.org/docs/api/fred/
- 覆盖：GDP、CPI、利率、就业、M2 等数千指标
```python
import subprocess, json
KEY = "YOUR_FRED_KEY"
data = subprocess.run(
    ['curl','-s',f'https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key={KEY}&file_type=json'],
    capture_output=True, text=True
).stdout
```
