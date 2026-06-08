# 评测系统

> PTCG-Bench 的评测管线：批量对战、指标收集、排行榜与对战回放。

---

## 目录

- [评测管线](#评测管线)
- [Metrics 指标](#metrics-指标)
- [排行榜](#排行榜)
- [对战回放](#对战回放)
- [Ablation 评测](#ablation-评测)
- [Anchored Evaluation](#anchored-evaluation)

---

## 评测管线

评测管线通过 `ptcgbench/bench/eval_pipeline.py` 提供 CLI 入口，支持：

- 任意两 Agent 的批量对战（round-robin）
- Glicko-2 评分系统
- 实时进度展示
- Weave 实验追踪

### 基本用法

```bash
# 简单对战
uv run python -m ptcgbench.bench.eval_pipeline --agents random random --n-games 20

# LLM Agent 对战
uv run python -m ptcgbench.bench.eval_pipeline \
  --agents react:deepseek-chat random --n-games 20

# 多 Agent 混战（round-robin）
uv run python -m ptcgbench.bench.eval_pipeline \
  --agents random charizard_heuristic react:deepseek-chat --n-games 10

# 查看排行榜
uv run python -m ptcgbench.bench.eval_pipeline --show
```

### 关键参数

| 参数 | 说明 |
|------|------|
| `--agents` | Agent 列表，格式：`agent_type[:model]` |
| `--n-games` | 每对 Agent 的对战局数 |
| `--deck` | 牌组文件路径（默认 Charizard ex） |
| `--seed` | 随机种子（用于可复现性） |
| `--show` | 显示排行榜 |
| `--harness` | 启用 Harness 模式（开发中） |

---

## Metrics 指标

`ptcgbench/bench/metrics.py::MetricsCollector` 收集每局指标：

### Per-Game Metrics

| 指标 | 类型 | 说明 |
|------|------|------|
| `winner_id` | str | 胜者 agent ID，或 "draw" |
| `steps` | int | 本局总步数 |
| `p1_rating_before/after` | float | 选手 1 Glicko-2 评分变化 |
| `p2_rating_before/after` | float | 选手 2 Glicko-2 评分变化 |

### Per-Batch Metrics

| 指标 | 说明 |
|------|------|
| `total` | 总局数 |
| `draws` | 平局数 |
| `avg_steps` | 平均步数 |
| `{agent}_wins` | 某 Agent 胜场数 |
| `{agent}_win_rate` | 某 Agent 胜率 |
| `rolling_win_rate(window=10)` | 最近 10 局滚动胜率 |

### 用法

```python
from ptcgbench.bench.metrics import MetricsCollector, GameMetrics

collector = MetricsCollector()
collector.record_game(GameMetrics(...))

# 查看摘要
print(collector.summary(agent_ids=["react", "random"]))

# 保存/加载
collector.save(Path("results.json"))
collector.load(Path("results.json"))
```

---

## 排行榜

基于 Glicko-2 评分系统的 Agent 排行榜。

位置：`ptcgbench/bench/glicko2.py` + `ptcgbench/bench/leaderboard.py`

```bash
# 查看排行榜
uv run python -m ptcgbench.bench.eval_pipeline --show
```

排行榜会自动追踪每个 Agent 的：
- Rating（评分）
- RD（评分偏差）
- Volatility（波动性）
- 对战次数、胜率

---

## 对战回放

每局对战自动保存为 JSONL 格式的录像文件。

### 回放文件位置

```
battle_log/seed_{seed}.jsonl
```

### JSONL 格式

每行一个 JSON 对象，包含：
- `event_type`: 事件类型（state_update / action / termination）
- `turn`: 当前回合
- `player`: 当前玩家
- `data`: 事件数据

### 回放检查

`ptcg/utils/replay_checker.py` 提供回放验证功能：

```python
from ptcg.utils.replay_checker import ReplayChecker

checker = ReplayChecker(seed=42)
# 验证回放一致性
```

### 问题检测

`ptcg/utils/issue_detector.py` 自动检测对局中的异常：

| 检测类型 | 说明 |
|---------|------|
| `softlock` | 60+ 步无伤害输出，疑似软锁 |
| `llm_anomaly` | LLM API 失败次数异常 |

---

## Ablation 评测

Ablation 评测通过切换 Harness Pipeline 中的模块来量化各组件对 Agent 表现的贡献。

### Ablation 模式

| 模式 | 说明 | 用途 |
|------|------|------|
| `full_harness` | 完整 Pipeline | baseline |
| `no_memory` | 禁用记忆检索 | 测量 Memory 贡献 |
| `no_structured_observation` | 简化 observation | 测量结构化 Observation 贡献 |
| `no_legal_action_mask` | 禁用合法动作列表 | 测量 Action Mask 贡献（Phase 2） |
| `no_history_context` | 禁用操作历史 | 测量 Context 贡献（Phase 2） |

### 运行 Ablation 评测

```bash
# Full harness
uv run python -m ptcgbench.bench.eval_pipeline \
  --agents harness_react:deepseek-chat harness_react:deepseek-chat \
  --harness --ablation full_harness --n-games 50

# No memory ablation
uv run python -m ptcgbench.bench.eval_pipeline \
  --agents harness_react:deepseek-chat harness_react:deepseek-chat \
  --harness --ablation no_memory --n-games 50
```

---

## Anchored Evaluation

Anchored Evaluation 通过固定 anchor agents + 固定牌组 + 固定 seed 来衡量 Agent 的真实技能水平，消除 deck matchup 等混淆因素。

### Mirror Match（最干净指标）

```bash
# Evolving Agent vs Frozen Baseline（同牌组）
uv run python -m ptcgbench.bench.anchored_eval \
  --agent harness_react:deepseek-chat \
  --deck charizard_ex \
  --n-games 50 --seeds 0,42,123
```

### 统计检验

使用 Binomial test（p < 0.05）判断胜率差异是否统计显著。
