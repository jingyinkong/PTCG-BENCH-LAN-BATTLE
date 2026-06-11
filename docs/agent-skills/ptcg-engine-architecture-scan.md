# PTCG Engine Architecture Scan

## 适用场景

这个 skill 用于在改动前扫描 `ptcg-engine` 的现有架构，并建立最小必要上下文。适用于以下场景：

- 分析 `ptcg-engine` 调用链
- 分析 `Action` / `reducer` / `card.reduce_action`
- 分析 `State` / `Player` / `Zone` / `move_cards`
- 分析卡牌效果实现模式
- 在任何重构前建立上下文

## 必读文件

在输出任何设计结论或改动建议前，至少阅读以下文件：

- `ptcg/core/action.py`
- `ptcg/core/envs.py`
- `ptcg/core/reducer.py`
- `ptcg/core/state.py`
- `ptcg/core/player.py`
- `ptcg/core/card.py`
- `ptcg/core/ops/types.py`
- `ptcg/core/ops/context.py`
- `ptcg/core/ops/zones.py`
- `ptcg/core/ops/executor.py`
- `ptcg/core/ops/resolver.py`
- `docs/semantic_operation_layer.md`
- `docs/CODEX.md`
- `docs/ARCHITECTURE.md`

如果本轮任务还涉及具体工具函数或单卡逻辑，再补读：

- `ptcg/utils/utils.py`
- 相关 `ptcg/cards/**` 文件
- 对应测试文件

## 扫描重点

### 1. 当前调用链

必须先确认当前引擎仍然是 source-driven reducer：

```text
env.step(action)
  -> _reduce_action
  -> action.source.reduce_action(action, state)
```

需要明确：

- `Action` 是玩家输入和交互意图
- `reduce_action` 是当前主执行入口
- generator `yield` / `yield from` 仍用于 choice 和多步交互
- 当前语义操作层只是旁路骨架，尚未接入主流程

### 2. State 与 Zone 模型

扫描时必须确认以下事实：

- `player.left` 是运行时牌库
- `player.deck` 更接近初始牌组或配置语义
- `move_cards` 是当前迁移的关键桥接点
- `active` / `bench` / `attachment` / `stadium` 的表达方式和约束不同
- `State` / `Player` / `utils` 中都可能存在直接状态修改点

### 3. 卡牌效果实现模式

需要识别当前卡牌效果一般落在什么位置：

- `card.get_actions()`
- `card.reduce_action()`
- `reducer.py` 中的流程函数
- `ptcg/utils/utils.py` 中的通用状态操作

并判断哪些逻辑将来可以抽象成 `GameOp`，哪些仍依赖 legacy generator / reducer。

## 禁止事项

除非用户明确要求，否则执行这个 skill 时：

- 不要修改代码
- 不要接入 `reducer`
- 不要修改 `env.step`
- 不要批量修改 `ptcg/cards`
- 不要替换 legacy `reduce_action`
- 不要改 `frontend` / `backend`
- 不要伪造测试结果

## 输出格式

输出结果必须使用以下结构，按顺序给出：

### 当前调用链

- 当前 `env.step` 如何到达状态修改
- `Action`、`source`、`reduce_action` 分别承担什么职责

### 直接 state 修改点

- 哪些函数直接改 `state` / `player`
- 哪些修改点在 `reducer.py`
- 哪些修改点在 `ptcg/utils/utils.py`
- 哪些修改点藏在单卡实现里

### 可抽象 GameOp

- 哪些状态变化适合抽成 `GameOp`
- 哪些是 `StateOp`
- 哪些隐含 `ChoiceOp`
- 哪些更像 `FlowOp`

### 高风险逻辑

- generator choice
- 击倒与替换 active
- 能量、进化、附着
- 场地、工具、递归委托
- 任何强依赖 legacy reducer 的路径

### 不建议本轮修改的模块

- 当前改动风险高或耦合重的模块
- 不应在本轮直接动的主流程文件

### 下一步最小安全改动

- 一次只做一个旁路能力
- 优先补类型、测试、文档，再考虑接缝
- 给出最小可验证的改动建议

## 检查清单

输出前必须自检以下问题：

- 是否识别 source-driven reducer
- 是否识别 generator choice
- 是否识别 `player.left` 是运行时牌库
- 是否识别 `move_cards` 是现有迁移核心
- 是否区分 `Action` 和 `GameOp`

如果以上任一项不能明确回答，应继续阅读代码，而不是直接给出重构建议。
