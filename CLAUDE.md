# CLAUDE.md

## 语言偏好

## 项目架构速查

本项目是一个宝可梦卡牌游戏平台，由四层组成：

| 层级 | 目录 | 技术 |
|------|------|------|
| **引擎层** | `ptcg/` | 游戏规则引擎（Action-Reducer 模式，Generator 状态机） |
| **AI层** | `ptcgbench/` | AI 智能体 + 评测管道 + 外部服务 |
| **服务层** | `backend/` | FastAPI 后端（REST + WebSocket PvP） |
| **展示层** | `frontend/` | React 18 SPA（Zustand 状态管理 + Tailwind CSS） |

**核心文件**：
- `docs/CODEX.md` — 完整代码框架总览（模块索引、数据流、耦合分析、增量指南）
- `docs/ARCHITECTURE.md` — 三层系统架构 + PvP 消息协议
- `AGENTS.md` — 项目级 AI Agent 指南（子目录均有对应 AGENTS.md）
- `ptcg/core/AGENTS.md` — 引擎核心详细说明（15 个模块、State Flow、Action 类型）

**添加新卡牌**：参见 `docs/ADDING_A_CARD.md`（含模板和验证清单）

**关键数字**：37 个扩展包 / ~210 张卡牌 / 8 种 AI Agent 策略 / 约 3300+ 测试用例


- **所有对话、回复、解释、任务描述必须使用简体中文。**
- 代码本身（变量名、函数名、日志信息等）保持英文不变。
- 命令行工具的 description 参数使用中文。
- 所有展示内容（包括表格、列表、提示等）使用中文。

## Bug 修复流程（防回归）

每次修 bug 必须按以下四步执行，禁止跳过任何一步：

### Step 1: 复现 bug
- 确认 bug 现象真实存在，理解触发条件

### Step 2: 判断问题 + 影响面分析
- 定位根因
- **影响面分析**（核心）：修改前系统性地评估被修改代码的影响范围
  - 跨文件搜索所有调用方（rg 函数名/方法名，优先使用 ripgrep）
  - 追踪被修改代码的上游（谁给它输入）和下游（它输出给谁）
  - 检查是否存在 monkey-patch 隐式耦合（`engine_patches.py` 中 `_original_*` 变量）
  - 修改判断逻辑时：追踪判断下的所有变量 → 检查下游消费者是否受影响
  - 修改函数签名时：搜索所有调用方，确认参数匹配
  - 新增代码行时：检查是否覆盖/干扰同位置已有操作（yield、状态赋值、回调）

### Step 3: 修复问题
- 写最小化的修复代码

### Step 4: 验证影响范围（循环直到完美）
- `uv run python -m pytest tests/ -q` 必须全绿
- **手动测试被修改功能的主流程**（如修投硬币 → 测"建游戏→选牌→投硬币→正常游戏"）
- **至少验证一条会经过修改点的关联路径**
- 提交前 checklist：
  - `git diff` 确认无意外改动
  - pytest 全绿
- 重启服务后确认修复生效且无新问题

### 核心原则

**追踪状态变更 → 找到所有消费者 → 验证不破坏**

分析时间上限：编写修复代码时间的 3 倍以内。

## OMC 模型路由速查

### 判断标准
该 agent 的核心任务是否需要深度语义理解、多步因果推理、或安全性敏感决策？
- 需要 → **Pro** (`deepseek-v4-pro`)
- 不需要 → **Flash** (`deepseek-v4-flash`)

### 🧠 Pro — 高认知负荷（调用时必须显式传 model）

| Agent | 理由 | model 参数 |
|-------|------|-----------|
| architect | 全局架构推理、多系统权衡 | `model="opus"` |
| planner | 多步规划、依赖分析、风险评估 | `model="opus"` |
| code-reviewer | 语义级 bug 检测、逻辑漏洞 | `model="sonnet"` |
| security-reviewer | 攻击面分析、安全漏洞识别 | `model="sonnet"` |
| debugger | 假设验证、因果链追踪、根因分析 | `model="sonnet"` |

### ⚡ Flash — 低认知负荷（走默认，无需传 model）

| Agent | 理由 |
|-------|------|
| explorer | 搜索/匹配为主 |
| executor | 机械性实现，遵循已有模式 |
| test-engineer | 模板化测试生成 |
| verifier | 验证已有结果、比对输出 |
| designer | 模板化 UI 输出 |
| writer | 文档生成、注释补全 |

### ⚠️ 手动升级触发条件

| Agent | 升级条件 |
|-------|---------|
| explorer | 追踪复杂调用链、跨模块依赖分析 → 加 `model="sonnet"` |
| executor | 复杂重构、跨多文件逻辑变更、算法实现 → 加 `model="sonnet"` |
| test-engineer | 复杂边界条件测试、并发测试设计 → 加 `model="sonnet"` |

### Skill 路由（继承所调用 Agent 的模型）

| Skill | 实际路由 |
|-------|---------|
| autopilot | planner(Pro) → executor(Flash) → code-reviewer(Pro) |
| ralph / ultrawork | executor(Flash) + architect(Pro) 验证 |
| team | 各 agent 按表独立路由 |
| deep-interview | 提问(Flash) + **评分(Pro 强制)** + 结晶(Pro) |

### 升级原则
默认按表执行。遇到以下信号时手动切换到 Pro：
1. Flash 输出连续 2 次不符合预期
2. 任务涉及跨 5+ 文件的复杂逻辑
3. 需要权衡多个冲突的架构决策

> 💡 如果使用 Flash agent 后觉得输出不够好，直接重新调用并加上 `model="sonnet"` — 不需要犹豫。

### 配置陷阱
`CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash` 是**全局默认**，影响所有 sub-agent。Pro agent 忘记传 `model` → 静默用 Flash → 质量下降。调用 Pro agent 时务必检查 `model` 参数。

## 文档路由表

<documentation_routing>
处理代码时按以下路由查阅文档，每个路径对应首选文档+备选文档：

| 工作目录/问题类型 | 首选文档 | 备选文档 |
|-----------|---------|---------|
| ptcg/core/ — 引擎核心、状态机、Action/Reducer | `ptcg/core/AGENTS.md` | `docs/CODEX.md` |
| ptcg/cards/ — 卡牌实现、效果逻辑 | `docs/ADDING_A_CARD.md` | `ptcg/cards/AGENTS.md` |
| backend/ — API、WebSocket、PvP服务 | `backend/AGENTS.md` | `docs/ARCHITECTURE.md` |
| frontend/ — React组件、状态管理 | `frontend/AGENTS.md` | — |
| ptcgbench/agents/ — AI Agent开发 | `docs/AI_AGENT.md` | `ptcgbench/agents/AGENTS.md` |
| ptcgbench/bench/ — 评测管道 | `docs/EVALUATION.md` | `ptcgbench/bench/AGENTS.md` |
| tests/ — 测试编写、框架 | `docs/DEVELOPMENT.md` | `tests/AGENTS.md` |
| docs/ — 用户使用/PvP | `docs/USER_GUIDE.md` | — |
| pyproject.toml / 项目配置 | `AGENTS.md` | — |
</documentation_routing>

## 文档维护规则

<documentation_maintenance>
完成代码变更后，按以下映射检查并更新关联文档：

### 按目录映射
| 变更目录 | 需检查的文档 |
|---------|------------|
| `ptcg/core/` | `ptcg/core/AGENTS.md` |
| `ptcg/cards/` | `docs/ADDING_A_CARD.md`（新增效果样例）+ `ptcg/cards/AGENTS.md` |
| `backend/` | `backend/AGENTS.md` |
| `frontend/` | `frontend/AGENTS.md` |
| `ptcgbench/agents/` | `docs/AI_AGENT.md` + `ptcgbench/agents/AGENTS.md` |
| `ptcgbench/bench/` | `docs/EVALUATION.md` + `ptcgbench/bench/AGENTS.md` |
| `tests/` | `docs/DEVELOPMENT.md` |

### 按变更类型映射
| 变更类型 | 需检查的文档 |
|---------|------------|
| 新增卡牌 | `docs/ADDING_A_CARD.md`（效果模式新到需加示例时） |
| 改引擎核心逻辑 | `docs/CODEX.md` + `ptcg/core/AGENTS.md` |
| 改 API/协议 | `docs/ARCHITECTURE.md` |
| 改测试框架 | `docs/DEVELOPMENT.md` |
| 新增 Agent 策略 | `docs/AI_AGENT.md` |
| 改前端组件 | `frontend/src/components/AGENTS.md` |

### 维护规则
1. 修改代码前先读关联文档，修改后同步更新
2. 如文档修改导致 `docs/CODEX.md` 对应章节过时，同步更新
3. AGENTS.md 修改后更新其头部时间戳
4. 不确定是否需要更新时，保守更新（宁可多更新不要漏）
</documentation_maintenance>

## 推荐工具

<recommended_tools>
以下工具已安装或推荐安装，优先使用它们进行搜索和文件操作：

| 工具 | 用途 | 状态 |
|------|------|------|
| `rg` (ripgrep) | 代码搜索，比 grep 快 5-10 倍，自动忽略 .gitignore | ✅ 已安装 (v13.0.0) |
| `fdfind` (fd) | 文件查找，比 find 快 5 倍，自动忽略 .gitignore | ✅ 已安装 |
| `bat` | 带语法高亮的文件查看器，cat 替代品 | 📦 推荐安装 |
| `jq` | JSON 命令行处理 | 📦 推荐安装 |

使用示例：
- 搜索代码: `rg "pattern" --include="*.py" -l`
- 查找文件: `fdfind "test_*.py" tests/`
- 查看文件: `bat CLAUDE.md`
- JSON处理: `cat data.json | jq '.field'`
</recommended_tools>
