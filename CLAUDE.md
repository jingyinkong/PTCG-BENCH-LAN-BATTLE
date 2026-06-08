# CLAUDE.md

## 语言偏好

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
  - 跨文件搜索所有调用方（grep 函数名/方法名）
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
