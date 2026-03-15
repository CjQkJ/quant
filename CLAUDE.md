# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目定位

本项目是一个加密货币市场分析工具集，以 CLI 和 MCP 形式提供各类分析 Skill。项目将持续扩展新的 Skill 和 MCP 模块。

## 常用命令

所有命令在 `crypto-skills-cli/` 目录下执行。

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 CLI（查看可用命令）
python main.py --help

# 烟测验证（确保依赖和模块导入正常）
python -c "from core.exchange_aggregator import FuturesAggregator; print('核心模块加载成功')"
```

各 Skill 的具体用法见 `docs/skills/` 下对应的文档。

## 架构概览

```
crypto-skills-cli/
├── core/                  # 核心基础设施（交易所连接、通用工具）
│   └── exchange_aggregator.py
├── skills/                # 分析 Skill 模块（每个 Skill 一个文件）
│   └── smart_liquidity.py
├── docs/                  # 文档目录
│   └── skills/            # 各 Skill 使用文档
├── main.py                # CLI 入口（typer + rich）
├── requirements.txt       # Python 依赖
└── environment.yml        # Conda 环境配置
```

### 分层职责

- **`core/`** — 可复用的基础设施层。`FuturesAggregator` 提供多交易所（Binance / Bybit / OKX）USDT 本位永续合约的统一连接、符号格式化、订单簿和行情数据拉取。新 Skill 应复用此层，不要重复造轮子。
- **`skills/`** — 业务分析层。每个 Skill 是一个独立模块，封装完整的分析流程，对外暴露一个主入口方法。
- **`main.py`** — CLI 交互层。使用 typer 注册子命令，每个 Skill 对应一个子命令，使用 rich 渲染输出。

### 新增 Skill / MCP 的完整流程

1. 在 `skills/` 下创建新模块文件
2. 复用 `core/` 的基础设施，如需扩展则在 `core/` 中添加
3. 在 `main.py` 中注册对应的 typer 子命令
4. 在 `docs/skills/` 下编写对应的中文使用文档
5. **代码审查 + 烟测验证，跑通全流程确认端到端可用后才算开发完成**
6. **立即部署适配到 Claude Code 中投入使用**：
   - Skill → 在 `.claude/skills/<skill-name>/SKILL.md` 创建配置文件
   - MCP → 在项目根目录 `.mcp.json` 或通过 `claude mcp add` 命令注册

开发完成 ≠ 交付完成。必须经过审查、烟测、全流程跑通，并配置到 Claude Code 后才算真正完成。

## 开发规范

### 中文要求（强制）

- **所有文档**使用中文（README、CLAUDE.md、docs/、SKILL.md 等）
- **代码注释和 docstring** 使用中文
- **CLI 输出信息和交互面板** 使用中文（包括帮助文本、错误提示、状态提示）
- **print / console 输出** 使用中文
- 除变量名、函数名、类名等代码标识符外，面向用户的一切文本均使用中文

### 质量要求（强制）

- 每个 Skill / MCP 开发完成后，**必须进行完整的代码审查和烟测验证**
- 烟测必须覆盖：模块导入 → CLI help → 端到端实际运行，全部通过才算合格
- 发现 bug 必须当场修复，不能留给后续处理
- 不明确的需求主动询问，不要自行假设

### 部署要求（强制）

- 每个 Skill / MCP 开发完成并通过烟测后，**必须立即部署适配到 Claude Code 项目中投入使用**
- Skill 配置到 `.claude/skills/<skill-name>/SKILL.md`
- MCP 配置到 `.mcp.json` 或通过 `claude mcp add` 注册

### 技术规范

- 交易所配置：Binance 用 `defaultType: 'future'`，Bybit 用 `'linear'`，OKX 用 `'swap'`
- `format_symbol()` 负责统一符号格式，支持任意大小写输入
- 使用 `ccxt.async_support` 异步并发拉取多交易所数据
