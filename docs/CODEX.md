# CODEX — PTCG-Bench 代码框架总览

> **最后更新**: 2026-06-11
> **目的**: 为开发者和 AI Agent 提供项目代码结构的全景视图，包括模块职责、关键文件索引、核心数据流和耦合关系。是 `docs/ARCHITECTURE.md` 的代码级补充。

---

## 1. 顶层项目结构

```
PTCG-BENCH-LAN-BATTLE/
├── ptcg/              # [引擎层] PTCG 游戏引擎（核心规则实现）
│   ├── core/          #   引擎核心：状态机、Action、Reducer
│   ├── cards/         #   卡牌实现（37 set / ~210 张卡）
│   ├── decks/         #   牌组定义文件（.txt 格式）
│   └── utils/         #   工具函数
├── ptcgbench/         # [AI层] AI 智能体 + 评测 + 服务
│   ├── agents/        #   AI Agent 实现（8 种策略）
│   ├── bench/         #   评测管道
│   └── services/      #   外部服务集成
├── backend/           # [服务层] FastAPI 后端（REST + WebSocket）
├── frontend/          # [展示层] React 18 前端 SPA
├── tests/             # 测试套件
├── scripts/           # 工具脚本（卡牌生成、审计、验证）
├── docs/              # 文档
├── battle_log/        # 对战日志（JSONL）
└── card_data/         # 卡牌图片缓存
```

### 三层调用关系

```
frontend/ (React SPA)  ── REST/WS ──▶ backend/ (FastAPI)
                                          │ import
                                          ▼
                                    ptcgbench/ (AI Agent + Bench)
                                          │ import
                                          ▼
                                    ptcg/ (游戏引擎)
                                          │
                                          └── ptcg-engine (外部库)
```

---

## 2. 核心引擎（ptcg/core/）

详见 `ptcg/core/AGENTS.md`。

引擎遵循 **Action-Reducer 模式** + **Generator 状态机**。共 15 个模块：`card.py`（卡牌基类体系）、`state.py`（游戏状态容器）、`player.py`（玩家区域管理）、`action.py`（15 种动作类型）、`reducer.py`（状态转换函数）、`attack.py`、`ability.py`（特性系统）、`enums.py`、`envs.py`（PokemonTCG Gymnasium-like API）、`card_registry.py`（自动注册）、`ability_handler.py`、`effect.py`、`reward.py`、`deck.py`、`recorder.py`、`exceptions.py`。

### 状态流转

```
env.reset()  → 创建玩家 → 洗牌发牌 → 设奖赏卡 → 选战斗宝可梦 → 抛硬币 → (obs, info)
env.step(action)  → 验证合法性 → reducer → 奖励 → 终止判断 → 记录 → (obs, reward, done, info)
```

---

## 3. 卡牌实现（ptcg/cards/）

详见 `ptcg/cards/AGENTS.md`。

- **37 个扩展包**（每包一个子目录），**约 210 张卡牌**（每卡一个 `.py` 文件）
- 最大系列：`PAR`（23 张）、`ASR`（22 张）、`TEF`（22 张）
- 基类继承：`Card (ABC)` → `PokemonCard` / `SupporterCard` / `ItemCard` / `StadiumCard` / `EnergyCard`
- 自动注册：`CardRegistry._scan_card_implementations()` 通过 `rglob("*.py")` + `importlib` 自动发现

### 数据源关系

```
TCGDex API (tcg.mik.moe)  →  gen_cards.py  →  ptcg/cards/{SET}/{name}.py  ←── SSOT
                                                              →  card_data_cache.json (派生缓存)
```

---

## 4. 智能体系统（ptcgbench/agents/）

详见 `docs/AI_AGENT.md`。

| Agent | 策略 | 依赖 LLM |
|-------|------|---------|
| `RandomAgent` | 随机选择合法动作 | 否 |
| `CharizardHeuristicAgent` | 基于规则的启发式策略 | 否 |
| `ReActAgent` | Thought-Action 循环 + Tool Calling | 是 |
| `ReflexionAgent` | ReAct + 赛后反思学习 | 是 |
| `LTMAgent` | ReAct + 长期记忆注入 | 是 |
| `SkillEvolvingAgent` | ReAct + 技能进化 | 是 |
| `PromptEvolvingAgent` | ReAct + 提示进化 | 是 |
| `ExpeLAgent` | 经验学习 | 是 |

子系统：`common/`（LLM 客户端工厂）、`interfaces/`（ToolCallExecutor + StateObserver）、`memory/`、`prompts/`、`skills/`、`tools/`、`trace/`。

---

## 5. 评测管道（ptcgbench/bench/）

| 模块 | 职责 |
|------|------|
| `eval_pipeline.py` | 批量对战调度、Agent 配对、结果收集 |
| `glicko2.py` | Glicko-2 评分系统 |
| `leaderboard.py` | Agent 评分排名 + 历史追踪 |
| `metrics.py` | 每局/每批指标（胜率、平均回合等） |
| `charting.py` | 可视化图表 |
| `plot_ratings.py` | 评分变化趋势图 |
| `live_progress.py` | Rich 终端进度显示 |

### 评估模式：Round-Robin / Ablation / Anchored

---

## 6. 后端服务（backend/）

详见 `backend/AGENTS.md`。

FastAPI 后端：`main.py`（路由注册 + WebSocket）、`auth.py`（JWT 认证）、`game_rooms.py`（房间 CRUD + GC）、`pvp_game.py`（WebSocket 消息路由）、`match_records.py`、`card_image_service.py`、`database.py`（SQLite）、`engine_patches.py`（monkey-patch）、`settings.py`、`i18n/`。

---

## 7. 前端应用（frontend/）

详见 `frontend/AGENTS.md`。

React 18 SPA（Vite + Tailwind CSS + Zustand）：5 个 Zustand store、22 个 UI 组件、i18n 双语支持、WebSocket 实时对战。

---

## 8. 测试体系（tests/）

```
tests/
├── conftest.py               # pytest 配置 + TestUtils 辅助
├── test_ai_battle_framework.py
├── test_auto_events.py
├── test_battle_log.py
├── agents/                   # Agent 系统单元测试（11 个文件）
├── bench/                    # 评测测试（2 个文件）
├── cards/generated/          # 自动生成卡牌测试（40 set 目录）
│   ├── test_{set}_{num}.py        # L1-L3 基础行为测试
│   ├── test_{set}_{num}_behavior.py  # L4-L6 深度行为测试
│   └── test_{set}_snapshot.py     # 快照回归测试
└── scripts/                  # 脚本测试
```

### 测试层级：**L1-L3** 基础行为 → **L4-L6** (behavior) 深度行为 → **Snapshot** 全量快照回归

---

## 9. 工具脚本（scripts/）

| 脚本 | 职责 |
|------|------|
| `gen_cards.py` | 从 TCGDex API 自动生成卡牌 Python 文件 |
| `merge_card_tests.py` | 测试文件合并 |
| `test_templates.py` | L1-L6 测试模板生成 |
| `verify_card_consistency.py` | 校验缓存与源码一致性 |
| `ast_effect_analyzer.py` | AST 分析卡牌效果模式 |
| `audit_card_patterns.py` | 卡牌实现模式审计 |
| `check_test_quality.py` | 测试质量检查 |
| `record_replay.py` | 对战回放录制 |
| `refresh_card_cache.py` | 卡牌数据缓存刷新 |
| `backfill_card_cache.py` | 卡牌图片缓存回填 |
| `git-ez.sh` | 一键 Git 提交 |

---

## 10. 核心数据流

### AI 对战数据流

```
LLM API (DeepSeek/Qwen/GLM...)
    ▲  tool call
    |
ModelClient
    ▲  提示词 + 观测
    |
[ReActAgent / etc.]
    ▲  predict(obs, info) → Action
    |
ToolCallExecutor → 匹配最佳合法动作
    |
PokemonTCG.step(action) → reduce_action → 状态更新 → 奖励 → 终止判断
    |
TraceRecorder → 记录每步推理和动作
```

### PvP 对战数据流

```
浏览器 A                   后端                   浏览器 B
  │                        │                       │
  │── WS CONNECT ────────►│◄────────────────── WS CONNECT ──│
  │◄─── COIN_TOSS ────────│─── COIN_TOSS ────────►│
  │─── COIN_TOSS_CALL ───►│─── COIN_TOSS ────────►│ (结果)
  │                        ├── engine_patches      │
  │                        │─── STATE_UPDATE ─────►│
  │◄─── STATE_UPDATE ─────│                       │
  │─── ACTION ───────────►├── env.step() ─────────│
  │                        │─── STATE_UPDATE ─────►│
  ...                    ...                      ...
```

---

## 11. 关键耦合分析

### 引擎-卡牌耦合三层模型

```
第 1 层: 工具函数      from ptcg.utils.utils import * (43 张卡 wildcard!)
第 2 层: Action 对象    AttackAction 等 13 种构造器（最多 149 次引用）
第 3 层: Reducer 函数   reduce_attack_action 等（最多 29 次引用）
```

### 引擎变更影响面

| 变更类型 | 影响范围 | 保护 |
|---------|---------|------|
| 工具函数签名变更 | 所有调用方 | 无 |
| Action 构造器变更 | 所有卡牌 + backend | 无 |
| Reducer 重命名 | 直接调用的卡牌 | 无 |
| State 内部结构变更 | 直接访问 state 的自定义效果 | 无 |
| 枚举值变更 | 所有引用 | 无 |

### 已知设计债务

1. **engine_patches.py** — 4 个 `_original_*` monkey-patch，应在引擎源码中解决
2. **Wildcard import** — 43 张卡使用 `from x import *`，隐藏实际依赖
3. **StopIteration 吞噬** — 测试中 63 处裸 `except StopIteration: pass`
4. **数据双源** — `card_data_cache.json` 和 Python 源码可能不一致
5. **样板代码** — 49 张卡显式初始化 `energy=[]`、`attachment=[]`、`evolved=[]`

---

> **相关文档**: `docs/ARCHITECTURE.md`（系统架构图）、`docs/DEVELOPMENT.md`（开发指南）、`docs/AI_AGENT.md`（Agent 开发）、`docs/ADDING_A_CARD.md`（新增卡牌指南）、`ptcg/core/AGENTS.md`（引擎详解）、`ptcg/cards/AGENTS.md`（卡牌详解）、`backend/AGENTS.md`（后端详解）、`frontend/AGENTS.md`（前端详解）
