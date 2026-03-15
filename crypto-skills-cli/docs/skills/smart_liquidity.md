# Smart Liquidity — 全网聚合流动性分析

## 功能概述

Smart Liquidity 是一个面向 HFT 级精度的永续合约流动性分析 Skill，实时聚合 Binance、Bybit、OKX 三家交易所的 USDT 本位永续合约数据。

### 核心能力

1. **聚合真实深度** — 并发拉取三家交易所的 L2 订单簿，合并后通过反幌骗过滤排除异常挂单，按可配置价格区间聚合
2. **未平仓量与杠杆热度** — 拉取全网 OI 和 Funding Rate，评估杠杆资金体量，推导多空情绪

## 使用方法

```bash
# 在 crypto-skills-cli/ 目录下执行
python main.py smart-liquidity --symbol BTC --threshold 74000 --bin-size 100
```

### 参数说明

| 参数 | 缩写 | 说明 | 默认值 |
|------|------|------|--------|
| `--symbol` | `-s` | 交易标的（如 BTC、ETH、SOL） | 必填 |
| `--threshold` | `-t` | 参考价格，用于反幌骗过滤基准 | 可选（默认用盘口中间价） |
| `--bin-size` | `-b` | 价格聚合区间大小（USDT） | 100 |

### 输出面板

1. **全网聚合卖盘挂单量 Top 3 价格区间** — 显示基础资产挂单量、USDT 名义价值与来源交易所
2. **全网聚合买盘挂单量 Top 3 价格区间** — 显示真实买盘支撑的数量与名义价值
3. **当前合约持仓量 (OI) 状态与多空情绪** — OI 汇总、资金费率、情绪判定
4. **交易所可用性提示** — 明确显示盘口来源、行情/OI 来源，以及任何降级或接口失败信息

### 快速测试

```bash
# 直接执行模块
python -m skills.smart_liquidity
```

## 技术细节

### 反幌骗机制

- 使用固定 5% 阈值（`SPOOF_THRESHOLD_PCT`）
- 仅保留参考价格上下 5% 范围内的报价
- `--threshold` 参数会覆盖盘口中间价作为过滤基准

### 情绪判定

基于三家交易所平均资金费率：
- `> 0.01%` → 看多（BULLISH）
- `< -0.01%` → 看空（BEARISH）
- 其他 → 中性（NEUTRAL）

### OI 计算

- OI 以基础资产单位（如 BTC）跨交易所求和
- 展示层乘以标记价格换算为 USDT 价值
- 若某家交易所只返回 OI 名义价值，则优先使用 `OI Value / Mark Price` 换算为基础资产数量

### 核心数据类型

- `LiquidityAnalysis` — 顶层结果，包含 `top_bid_buckets`、`top_ask_buckets`、`oi_total`、`mark_price`、`funding_rate_avg`、`sentiment`
- `LiquidityBucket` — 价格区间及其聚合的买卖挂单量与来源交易所标签
- `AggregatedOrderBook` — 合并后的订单簿，含 bids、asks、mid_price
