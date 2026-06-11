# Semantic Operation Layer 设计说明

## 背景

当前引擎采用 source-driven reducer 路径：

```text
env.step(action)
  -> _reduce_action
  -> action.source.reduce_action(action, state)
```

这条路径以 `Action` 为入口，由 `action.source` 决定如何修改状态。它已经支撑了当前大部分游戏流程，但状态变更语义仍然分散在 reducer、player 和单卡实现中。

## 问题

当前架构存在以下问题：

- 卡牌效果分散在单卡 `reduce_action` 中，难以统一抽象和复用。
- 状态修改入口不统一，迁移或审计状态变化成本较高。
- `auto_events` 主要是字符串或弱结构事件，不利于稳定消费和后续桥接。
- generator choice 机制深度嵌入 reducer，难以直接替换为统一语义层。
- `effect_primitives.py` 已经展示了可复用操作原语的价值，但尚未统一接入主执行路径。

## 目标架构

目标是逐步形成如下链路：

```text
Action
  -> Resolver
  -> GameOp[]
  -> OperationExecutor
  -> State mutation + OperationEvent[]
```

其中：

- `Resolver` 负责把玩家意图或卡牌效果解析成一组语义化操作。
- `GameOp` 负责表达要发生什么状态变化。
- `OperationExecutor` 负责执行这些操作。
- `OperationEvent` 负责产出结构化事件，供日志、回放、前后端和 AI 未来桥接使用。

## Action 与 GameOp 的区别

- `Action` 表示玩家意图，例如攻击、贴能量、选择卡牌。
- `GameOp` 表示状态变化语义，例如移动卡牌、造成伤害、附加特殊状态。

两者不是替代关系，而是不同层级的抽象：

- `Action` 面向输入和交互。
- `GameOp` 面向执行和状态语义。

## GameOp 分类

第一版按职责分为三类：

- `StateOp`：直接表达状态变化，例如移动卡牌、造成伤害、回复生命。
- `ChoiceOp`：表达需要显式选择的操作，例如从牌库搜索、从候选集中选牌。
- `FlowOp`：表达流程控制和事件编排，例如回合结束、递归委托、场地生命周期处理。

## 第一批操作优先级

### P0

- `move_cards`
- `draw_cards`
- `discard_cards`
- `play_pokemon`
- `evolve_pokemon`
- `attach_energy`
- `deal_damage`
- `apply_special_condition`
- `end_turn`

### P1

- `choose_cards`
- `search_deck`
- `switch_active`
- `take_prize`
- `recover_energy`
- `heal`
- `knockout`

### P2

- `coin_flip`
- `stadium_lifecycle`
- `on_knocked_out_tool`
- `lost_zone`
- `recursive_delegation`

## 第一阶段边界

第一阶段只做类型骨架和文档，不接入任何现有业务路径，边界如下：

- 不修改 `reducer`
- 不接入 `env.step`
- 不修改任何卡牌
- 不替换 `choose_card_actions` generator
- 不改变现有行为

这意味着第一阶段的产物仅用于定义语义层的稳定边界，为后续迁移做准备。

## 后续迁移路线

- 阶段 1：类型骨架
- 阶段 2：`ZoneService` + `OperationEvent`
- 阶段 3：基础 `OperationExecutor`
- 阶段 4：legacy fallback 接入
- 阶段 5：迁移简单卡
- 阶段 6：复杂卡和 AI 语义提取

## 第一阶段新增内容

本阶段新增以下能力，但都不直接参与当前执行流程：

- `ptcg.core.ops.types`：定义 `GameOp`、`OpType`、`ZoneRef`、`TargetRef`、`OpResult`
- `ptcg.core.ops.context`：定义 `ResolverContext` 与 `ExecutionContext`
- `ptcg.core.ops.events`：定义 `OperationEvent`、事件类型和事件收集器
- `ptcg.core.ops.errors`：定义语义操作层异常体系
- `ptcg.core.ops.__init__`：提供第一阶段常用导出入口

## 设计原则

- 先定义稳定接口，再逐步引入执行器。
- 尽量避免直接依赖具体 `Card`、`Player`、`State` 类，降低循环依赖风险。
- 事件结构保持强类型、低耦合，便于未来桥接旧事件系统。
- 允许与现有 generator reducer 并存，在迁移期通过桥接逐步替换。

## 迁移收益

如果后续迁移顺利完成，语义层将带来以下收益：

- 状态变化入口更统一，便于审计与调试。
- 卡牌效果表达更可组合，便于抽取共性模板。
- 结构化事件更利于回放、可视化和 AI 消费。
- 为 legacy reducer 到新执行层的分阶段迁移提供清晰边界。
