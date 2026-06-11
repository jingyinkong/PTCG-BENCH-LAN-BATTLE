# Semantic Operation Layer Design

## 适用场景

这个 skill 用于指导后续语义操作层的设计与实现。适用于以下场景：

- 新增 `GameOp`
- 扩展 `OperationExecutor`
- 扩展 `ZoneService`
- 新增 `Resolver`
- 设计 legacy fallback
- 迁移单张卡牌到 `resolve_ops`

## 当前架构原则

设计和实现时必须遵守以下原则：

- `Action` 是玩家意图
- `GameOp` 是状态变化语义
- `OperationResolver` 只负责 `Action` / `Card effect -> GameOp[]`
- `OperationExecutor` 只负责 `GameOp -> state mutation + OperationEvent`
- `ZoneService` 是统一区域访问入口
- 当前所有 `ops` 都是旁路，不接主流程

进一步约束：

- `Resolver` 不能直接修改 `state`
- `Executor` 不负责解析自然语言
- `ZoneService` 不替换 legacy `move_cards`
- 所有新能力先保持旁路，再考虑接缝

## 必读文件

在设计或实现任何语义操作层扩展前，至少阅读：

- `ptcg/core/ops/types.py`
- `ptcg/core/ops/context.py`
- `ptcg/core/ops/events.py`
- `ptcg/core/ops/errors.py`
- `ptcg/core/ops/zones.py`
- `ptcg/core/ops/executor.py`
- `ptcg/core/ops/resolver.py`
- `docs/semantic_operation_layer.md`
- `tests/core/test_ops_zone_service.py`
- `tests/core/test_operation_executor.py`
- `tests/core/test_operation_resolver.py`

如果准备接近 legacy fallback，再补读：

- `ptcg/core/action.py`
- `ptcg/core/reducer.py`
- `ptcg/utils/utils.py`

## 设计边界

扩展时必须遵守以下硬边界：

- 不支持的 `op` 必须显式抛 `InvalidOperationError`
- 不要吞异常
- 不要写 `state.auto_events`
- 不要直接调用 `reduce_action`
- 不要解析自然语言
- 不要读取 `card_data_cache`
- 不要调用 LLM
- 不要默认迁移卡牌
- 不要把 `deck` 当运行时牌库，运行时牌库是 `left`

同时注意：

- `count=N` 这类需要选择语义的行为，不能偷偷简化成“取前 N 张”
- 复杂区域如 `active` / `attachment` / `stadium` 不要在没有安全约束前直接支持移动
- 如果需要 fallback，也必须是显式桥接，而不是隐式混用

## 扩展 GameOp 的流程

新增一个 `GameOp` 时，按以下顺序推进：

1. 先补类型
2. 再补 executor 分支
3. 再补单元测试
4. 再补文档
5. 最后才考虑 resolver 或 legacy fallback

推荐执行方式：

- 先在 `types.py` 里定义或补充 `OpType`、参数约定和必要引用
- 再在 `executor.py` 中增加显式分支
- 为成功路径、失败路径和边界条件补测试
- 在 `docs/semantic_operation_layer.md` 记录能力边界
- 最后再判断该 `op` 是否值得纳入 `Resolver` 或 fallback

## 迁移卡牌的流程

迁移单张卡牌到 `resolve_ops` 时，按以下顺序推进：

1. 先选简单卡
2. 新增 `resolve_ops`
3. 只返回 `GameOp`，不直接改 `state`
4. 用旁路测试验证 `OperationExecutor` 行为
5. 最后才考虑接入 legacy fallback

选卡建议：

- 优先只含 `move_cards` / `draw_cards` / `discard_cards` 的简单 Trainer 或基础效果
- 避免一开始处理复杂 choice、伤害、击倒、进化或递归触发卡
- 不要批量迁移卡牌

## 常见错误

后续扩展时要特别避免以下错误：

- 直接改 `reducer`
- 直接改 `env.step`
- 批量改 `cards`
- 让 `resolver` 执行状态修改
- 让 `executor` 解析自然语言
- 偷偷支持复杂 choice
- 把 `count=N` 弃牌默认实现成弃前 `N` 张

还要避免：

- 在 `Executor` 里静默忽略不支持的 `op`
- 在 `Resolver` 里偷偷调用 `reduce_action`
- 在没有测试的情况下扩大 `ZoneService` 支持范围

## 输出格式

当使用这个 skill 产出设计或实现方案时，输出必须包含：

### 本次目标

- 本轮要解决什么问题
- 为什么现在做这一步

### 允许修改文件

- 本轮允许动哪些文件
- 为什么这些文件属于安全范围

### 禁止修改文件

- 哪些主流程文件、卡牌目录或外部层不得修改

### 设计方案

- 类型怎么扩展
- `ZoneService` / `Executor` / `Resolver` 哪一层负责什么
- 哪些能力暂不支持

### 测试方案

- `py_compile`
- 对应单元测试
- 边界条件和异常路径验证

### 风险和暂不处理内容

- 当前方案的限制
- 本轮明确不解决的问题
- 后续阶段才处理的内容

## 建议工作流

如果用户要推进语义操作层，优先采用下面的最小安全顺序：

1. 先确认本轮目标只落在单一旁路能力
2. 先阅读相关 `ops` 文件和现有测试
3. 只修改允许的最小文件集合
4. 先补测试，再验证行为边界
5. 最后明确说明“是否改动现有行为”

如果无法保证“不改现有行为”，应先停下来缩小范围，而不是继续扩大实现。
