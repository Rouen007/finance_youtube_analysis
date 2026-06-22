# Trading Knowledge Base

Prior knowledge for financial video summarization. The LLM should use these mappings to resolve ambiguous terms.

## Common Ticker Slang (Chinese)

| Slang | Ticker | Name |
|---|---|---|
| 按摩店 | AMD | Advanced Micro Devices |
| 闪迪 | SNDK | SanDisk |
| 软子 | 9984.T | SoftBank |
| 银子 | SLV | Silver ETF |
| 大饼 | BTC | Bitcoin |
| 二饼 | ETH | Ethereum |
| 纳指 | QQQ / NQ=F | Nasdaq 100 |
| 标普 | SPY / ES=F | S&P 500 |
| 道指 | DIA / YM=F | Dow Jones |
| 罗素 | IWM | Russell 2000 |
| 三倍纳指 | TQQQ | ProShares UltraPro QQQ |
| 三倍标普 | UPRO | ProShares UltraPro S&P500 |
| 恐慌指数 | VIX | CBOE Volatility Index |
| 美元指数 | DXY | US Dollar Index |
| 国债 | TLT / ZB=F | 20Y Treasury Bond |
| 黄金 | GLD / GC=F | Gold |
| 原油 | USO / CL=F | Crude Oil |
| 天然气 | UNG / NG=F | Natural Gas |

## Options Terminology

| Term | Meaning |
|---|---|
| Call | 看涨期权 |
| Put | 看跌期权 |
| Long call | 买入看涨（做多） |
| Long put | 买入看跌（做空/对冲） |
| Covered call | 备兑看涨（持有正股卖call） |
| Cash secured put | 卖看跌（愿意接盘） |
| Spread | 价差策略 |
| Straddle | 同时买call和put（赌波动） |
| Iron condor | 铁鹰策略（卖波动） |
| Butterfly | 蝶式策略 |
| LEAPS | 长期期权（1年+） |
| 0DTE | 当日到期期权 |
| 1DTE | 次日到期期权 |
| ATM | 平值期权（at the money） |
| ITM | 实值期权（in the money） |
| OTM | 虚值期权（out of the money） |
| Delta | 期权对股价敏感度 |
| Gamma | Delta的变化率 |
| Theta | 时间衰减 |
| IV | 隐含波动率 |
| IV crush | 财报后IV骤降 |
| OPEX | 期权到期日（月度第三个周五） |
| Max pain | 最大痛点价（期权卖方最优） |
| GEX | Gamma Exposure（做市商对冲压力） |
| Unusual options activity | 异常期权交易量 |

## Market Structure Terms

| Term | Meaning |
|---|---|
| 盘前 | Pre-market (4:00-9:30 ET) |
| 开盘 | Market open (9:30 ET) |
| 盘中 | Regular hours (9:30-16:00 ET) |
| 盘后 | After-hours (16:00-20:00 ET) |
| 四巫日 | Quad Witching (季度第三个周五，index/stock futures + options同时到期) |
| OPEX | Options Expiration |
| FOMC | Fed利率决议 |
| CPI | 通胀数据 |
| PPI | 生产者物价指数 |
| NFP | 非农就业数据 |
| GDP | 国内生产总值 |
| PCE | 个人消费支出（Fed首选通胀指标） |
| Earnings | 财报季 |
| Guidance | 公司前瞻指引 |
| Buyback | 回购 |
| Dividend | 分红 |
| Split | 拆股 |
| Reverse split | 缩股 |
| Short squeeze | 逼空 |
| Gamma squeeze | 伽马逼空（做市商被迫对冲） |
| Liquidity | 流动性 |
| Breadth | 市场宽度（涨跌家数比） |
| Rotation | 板块轮动 |
| Risk-on | 风险偏好（买股票/商品） |
| Risk-off | 风险规避（买国债/美元/黄金） |

## Technical Analysis

| Term | Meaning |
|---|---|
| Support | 支撑位 |
| Resistance | 阻力位 |
| Breakout | 突破 |
| Breakdown | 跌破 |
| Moving average (MA) | 均线 |
| VWAP | 成交量加权均价 |
| RSI | 相对强弱指标 |
| MACD | 移动平均收敛发散 |
| Volume | 成交量 |
| Gap | 缺口 |
| Fill the gap | 回补缺口 |
| Higher high / Higher low | 高点更高/低点更高（上升趋势） |
| Lower high / Lower low | 高点更低/低点更低（下降趋势） |
| Consolidation | 盘整/横盘 |
| Accumulation | 吸筹 |
| Distribution | 派发 |

## Risk Assessment Framework

When summarizing, always check:

1. **Concentration risk** — 单一标的仓位过重
2. **Chasing risk** — 已大涨后追高
3. **Event risk** — 财报/FOMC/CPI前持仓
4. **Liquidity risk** — 小盘股/低成交量期权
5. **Leverage risk** — 三倍ETF/0DTE/高杠杆
6. **Time decay** — 短期期权theta吃掉利润
7. **Promotion risk** — 视频是否含付费推广（需标注）
