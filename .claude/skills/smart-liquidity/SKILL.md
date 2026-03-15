---
name: smart-liquidity
description: 分析加密货币永续合约全网聚合流动性。当用户需要查看某个币种的订单簿深度、卖盘买盘压力、未平仓量(OI)、资金费率、多空情绪时触发。该 Skill 为自包含结构，执行脚本与说明都在本目录内。
argument-hint: "<币种> [参考价格] [区间大小]"
---

# Smart Liquidity

本 Skill 分析指定币种在 Binance、Bybit、OKX 三家交易所 USDT 本位永续合约的聚合流动性。

## 目录结构

```text
smart-liquidity/
├── SKILL.md
├── references/
│   ├── methodology.md
│   └── output-contract.md
└── scripts/
    ├── exchange_aggregator.py
    ├── smart_liquidity.py
    ├── run_analysis.py
    └── requirements.txt
```

## 前提检查

- `python --version` 必须 >= 3.10
- 若 `python scripts/run_analysis.py --help` 报缺依赖，先执行：

```bash
pip install -r E:/quant/.claude/skills/smart-liquidity/scripts/requirements.txt
```

- 如需代理访问交易所接口，可设置：

```bash
set CRYPTO_PROXY=http://127.0.0.1:7897
```

- 如需强制直连，可设置：

```bash
set CRYPTO_PROXY=none
```

## 执行顺序

1. 先读 `references/methodology.md`
2. 再读 `references/output-contract.md`
3. 解析 `$ARGUMENTS`，提取：
   - 币种（必填）
   - 参考价格（可选）
   - 区间大小（可选，默认 100）
4. 运行本 Skill 自带脚本：

```bash
python E:/quant/.claude/skills/smart-liquidity/scripts/run_analysis.py --symbol <币种> [--threshold <参考价格>] [--bin-size <区间大小>] --json
```

5. 基于脚本输出结果，给出「数据 + 结论」格式化分析

## 输出要求

必须先汇报数据，再给判断。

### 数据部分

- 标记价格
- 全网 OI
- 平均资金费率
- 多空情绪
- Top 3 卖盘压力区间
- Top 3 买盘支撑区间
- 实际成功接入的盘口来源
- 实际成功接入的行情/OI 来源
- 如有降级，列出失败交易所和原因

### 结论部分

- 压力位与支撑位离当前价格的关系
- OI 对杠杆拥挤度的含义
- 资金费率是否过热或过冷
- 当前偏多 / 偏空 / 中性判断
- 风险提示

## 执行准则

- 不要调用 `crypto-skills-cli/` 下的外部入口，本 Skill 已经自带执行工具
- 不要忽略交易所降级信息
- 不要把基础资产数量误写成 USDT 数量
- 若脚本报错，先向用户说明错误，再决定是否重试或降级

## 示例

用户输入：

```text
/smart-liquidity BTC 84000 100
```

执行：

```bash
python E:/quant/.claude/skills/smart-liquidity/scripts/run_analysis.py --symbol BTC --threshold 84000 --bin-size 100 --json
```
