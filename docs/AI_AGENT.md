# AI Agent

> PTCG-Bench 的 AI 智能体体系：Agent 类型、接入方式、Model Client 与 Agent 开发指南。

---

## 目录

- [Agent 类型总览](#agent-类型总览)
- [BaseAgent 接口](#baseagent-接口)
- [Agent 接入方式](#agent-接入方式)
- [Model Client](#model-client)
- [核心组件](#核心组件)
- [开发新 Agent](#开发新-agent)

---

## Agent 类型总览

| Agent | 文件 | 特点 |
|-------|------|------|
| **RandomAgent** | `random_agent.py` | 随机选择合法动作，baseline |
| **CharizardHeuristicAgent** | `charizard_heuristic_agent.py` | 规则启发式，不依赖 LLM |
| **ReActAgent** | `react_agent.py` | Thought→Action 循环，Tool Calling |
| **ReflexionAgent** | `reflexion_agent.py` | ReAct + 赛后 LLM 反思 |
| **LTMAgent** | `ltm_agent.py` | ReAct + 长期记忆注入 |
| **SkillEvolvingAgent** | `skill_evolving_agent.py` | ReAct + 技能进化 |
| **PromptEvolvingAgent** | `prompt_evolving_agent.py` | ReAct + 提示进化 |
| **ExpeLAgent** | `expel_agent.py` | 经验学习 |

---

## BaseAgent 接口

所有 Agent 的抽象基类定义在 `ptcgbench/agents/base_agent.py`：

```python
class BaseAgent(ABC):
    def predict(self, obs: State, info: Dict) -> Action:
        """核心决策：给定游戏状态，返回一个合法动作"""
        ...

    def reset(self) -> None:
        """重置 Agent 内部状态（每局开始时调用）"""
        ...

    def notify_game_start(self, my_deck, opponent_deck, opponent_name) -> None:
        """通知 Agent 对局开始（含牌组信息）"""
        ...

    def post_game(self, result, my_prizes, opponent_prizes) -> None:
        """通知 Agent 对局结束（用于反思/记忆更新）"""
        ...

    def post_batch(self, battle_summary, history_path) -> Optional[Dict]:
        """批量对局结束后的回调（用于批量学习）"""
        ...
```

### 对战流程中的 Agent 生命周期

```
notify_game_start() → reset() → [predict() × N] → post_game() → post_batch()
```

---

## Agent 接入方式

### 通过评测管线运行

```bash
# 两 Agent 对战
uv run python -m ptcgbench.bench.eval_pipeline --agents random random --n-games 20

# LLM Agent 对战（指定 model）
uv run python -m ptcgbench.bench.eval_pipeline \
  --agents react:deepseek-chat react:deepseek-chat --n-games 10

# 混合类型对战
uv run python -m ptcgbench.bench.eval_pipeline \
  --agents react:deepseek-chat random --n-games 20
```

### 通过代码直接使用

```python
from ptcg.core.envs import PokemonTCG
from ptcgbench.agents.random_agent import RandomAgent
from ptcgbench.agents.react_agent import ReActAgent

env = PokemonTCG(seed=42)
agent1 = ReActAgent(model="deepseek-chat")
agent2 = RandomAgent()

obs, _, done, info = env.reset()
while not done:
    action = agent1.predict(obs, info)
    obs, reward, done, info = env.step(action)
```

---

## Model Client

统一的多 provider LLM 客户端，位于 `ptcgbench/agents/common/model_client.py`。

### 支持的 Provider

| Provider | Model ID 示例 |
|----------|-------------|
| DeepSeek | `deepseek-chat`, `deepseek-v4-pro`, `deepseek-v4-flash` |
| Qwen (DashScope) | `qwen3.5-flash` |
| GLM (Z.AI) | `glm-4.7` |
| MiniMax | `MiniMax-M2.5` |
| OpenRouter | 所有 `OPENROUTER_BACKBONE_MODELS` |

### 核心 API

```python
from ptcgbench.agents.common.model_client import build_client, chat_completion_with_retry

# 创建客户端（自动解析 API key）
client = build_client("deepseek-chat")

# 带重试的调用（指数退避，最多 5 次）
response = chat_completion_with_retry(
    client,
    model="deepseek-chat",
    messages=[...],
    tools=[...],
    temperature=0.7,
)
```

### API Key 配置

API Key 通过环境变量配置：

| Model | 环境变量 |
|-------|---------|
| `deepseek-*` | `DEEPSEEK_API_KEY` |
| `qwen*` | `DASHSCOPE_API_KEY` |
| `glm-*` | `ZAI_API_KEY` |
| `MiniMax-*` | `MINIMAX_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |

也可以通过数据库设置页面配置（优先级低于环境变量）。

---

## 核心组件

### StateObserver

将 PTCG 引擎的 `State` 对象转换为 LLM 友好的结构化 `StateObservation`（Pydantic model）。

位置：`ptcgbench/agents/interfaces/observer.py`

### StateObservation Schema

定义 observation 的结构化字段（Pydantic BaseModel）。

位置：`ptcgbench/agents/interfaces/schema.py`

### Tool Calling

LLM Agent 通过 OpenAI Function Calling 选择游戏动作。Tool definitions 定义在 `ptcgbench/agents/tools/tool_schemas.py`，由 `ToolDispatcher` 执行。

### Memory System

| 组件 | 文件 | 功能 |
|------|------|------|
| MemoryStore | `memory/long_term_memory.py` | JSON 持久化记忆存储 |
| MemoryRetriever | `memory/long_term_memory.py` | 基于标签的相关记忆检索 |
| MemoryWriter | `memory/long_term_memory.py` | LLM 驱动的记忆提取与写入 |
| ContextManager | `memory/context_manager.py` | 本局操作历史滑动窗口 |

### Trace System

| 组件 | 文件 | 功能 |
|------|------|------|
| TraceRecorder | `trace/recorder.py` | Agent 推理轨迹记录 |
| TraceExtractor | `trace/extractor.py` | 轨迹数据提取与分析 |
| GameTrace | `trace/schema.py` | 轨迹数据 schema |

---

## 开发新 Agent

### 最小实现

```python
from ptcgbench.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def predict(self, obs, info):
        actions = info.get("raw_available_actions", [])
        return actions[0]  # 选择第一个合法动作
```

### 接入评测管线

1. 在 `ptcgbench/agents/` 下创建 Agent 文件
2. 在 `ptcgbench/bench/eval_pipeline.py` 的 agent factory 中注册
3. 通过 CLI 运行：`--agents my_agent:<model> random`

### 注意事项

- **不要直接修改游戏状态**：Agent 只能通过返回 Action 影响游戏
- **合法动作校验**：所有动作应来自 `info["raw_available_actions"]`
- **超时处理**：LLM Agent 应设置合理的 API 超时和重试策略
- **温度参数**：评测时建议使用较低温度（0.3-0.7）确保可复现性
