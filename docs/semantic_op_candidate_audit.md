# Semantic Operation Candidate Audit

## 目标

本报告仅用于筛选未来可能迁移到 `resolve_ops` 的简单真实卡牌候选，不做任何代码迁移。

本阶段只做审计，不修改任何卡牌实现，不修改 `ptcg/core` 生产代码，不接入 `SemanticReducerBridge` 到主流程，不改 `reducer`、`env.step` 或 `_reduce_action`。

## 当前可执行语义层能力

当前旁路语义层安全支持的 `StateOp` 只有：

- `move_cards`
- `draw_cards`
- `discard_cards`

当前 bridge 约束也很严格：

- 只允许 `OpCategory.STATE_OP`
- 拒绝 `ChoiceOp`
- 拒绝 `FlowOp`
- 拒绝 `requires_choice=True`
- 拒绝 `optional=True`
- 拒绝带 `condition` 的 `GameOp`
- 遇到非白名单 `op.type` 时直接抛出 `InvalidOperationError`

结合 `OperationExecutor`、`SemanticReducerBridge` 和现有 fake integration 测试，当前可安全旁路验证的真实卡牌候选必须尽量收敛到纯区域移动，不依赖 choice、generator、伤害结算、附能、进化、场地生命周期或 lost zone。

## 扫描方法

扫描范围：

- `ptcg/cards/**/*.py`

主要使用的搜索模式：

- `def reduce_action`
- `move_cards`
- `draw`
- `discard`
- `yield`
- `yield from`
- `choose_card_actions`
- `reduce_choose_card_actions`
- `flip_coin`
- `reduce_attack_action`
- `AttachEnergyAction`
- `EvolvePokemonAction`
- `on_knocked_out`
- `LOSTZONE`
- `lostZone`
- `Search`
- `shuffle`

人工复核策略：

- 先用文本搜索缩小范围，优先看不含 `yield` 的 `reduce_action`
- 再人工阅读高信号候选文件，确认是否真的只做简单区域移动
- 对所有看起来“接近简单”的实现，再二次检查是否隐藏了 prize、shuffle、opponent 区域、bench、choice、search 或条件逻辑
- 对 P0 采取保守标准，只保留不需要扩展 bridge safety gate 的候选

人工复核过的代表性文件包括：

- `ptcg/cards/TWM/twm145carmine.py`
- `ptcg/cards/SSH/ssh178professorsresearch.py`
- `ptcg/cards/PAF/professors_research.py`
- `ptcg/cards/FLI/fli108judge.py`
- `ptcg/cards/PAL/pal185iono.py`
- `ptcg/cards/ASR/asr150roxanne.py`
- `ptcg/cards/ASC/lillies_determination.py`
- `ptcg/cards/CRZ/energy_retrieval.py`
- `ptcg/cards/SFA/night_stretcher.py`
- `ptcg/cards/SIT/capturing_aroma.py`
- `ptcg/cards/PAF/rare_candy.py`
- `ptcg/cards/CRZ/lost_vacuum.py`
- `ptcg/cards/PAL/bosss_orders.py`
- `ptcg/cards/BRS/collapsed_stadium.py`
- `ptcg/cards/TEF/heavy_baton.py`
- `ptcg/cards/PAR/par170professorsadasvitality.py`

## P0 候选卡

P0 只保留“固定次序的 hand -> discard + left -> hand”这类最小闭环；即使实现很短，只要夹带 `shuffle`、奖赏卡数量分支、对手区域修改或任何选择语义，都不进入 P0。

| card file | card name/class | observed pattern | suggested ops | why safe | notes |
| --------- | --------------- | ---------------- | ------------- | -------- | ----- |
| `ptcg/cards/TWM/twm145carmine.py` | `TWM145Carmine` | 使用 Supporter 后先把自身从手牌移到弃牌区，再把剩余手牌全部丢弃，最后从 `left` 抽 5 张到手牌 | `move_cards` for supporter self, `discard_cards(count="all")`, `draw_cards(count=5)` | 不含 `yield`、`choose_card_actions`、`shuffle`、`coin_flip`、`search deck`、`reduce_attack_action`、bench/active/stadium/lost zone 路径；核心状态变化完全落在 `hand -> discard` 和 `left -> hand` | legacy 代码还会设置 `player.supporterPlayedTurn = True`，这不是当前 bridge 可表达的状态语义；下一阶段旁路测试应先聚焦区域变化与事件 |
| `ptcg/cards/SSH/ssh178professorsresearch.py` | `SSH178ProfessorsResearch` | 使用 Supporter 后先弃置自身，再把整手手牌丢弃，然后从 `left` 抽 7 张到手牌 | `move_cards` for supporter self, `discard_cards(count="all")`, `draw_cards(count=7)` | 与当前 executor 白名单完全对齐，且没有 choice、条件、对手区域修改或额外规则流程 | `ptcg/cards/PAF/professors_research.py` 是同模式重复实现，可视为同一迁移模板的第二个文件 |

## P1 候选卡

P1 表示“逻辑仍然相对短，但要么有轻微条件，要么需要 `shuffle` / opponent-side 语义，要么 draw count 依赖 prize 等外部状态”，当前不适合直接进入 bridge 白名单。

| card file | card name/class | observed pattern | suggested ops | risk | notes |
| --------- | --------------- | ---------------- | ------------- | ---- | ----- |
| `ptcg/cards/FLI/fli108judge.py` | `FLI108Judge` | 双方玩家都把手牌放回 `left`，重洗后各抽 4 张 | 未来可能需要 `move_cards` + `draw_cards`，外加显式 `shuffle_deck` 或 flow-like deck reorder op | 当前语义层没有 `shuffle`；同时涉及对手区域的双边修改，不是最小 P0 | 无 generator，但不是纯区域移动模板 |
| `ptcg/cards/PAL/pal185iono.py` | `PAL185Iono` | 双方把手牌放回 `left`，然后按各自 prize 数抽牌，再洗牌 | 未来可能需要 `move_cards` + `draw_cards` + `shuffle_deck` + count-from-state | draw count 依赖 `prize`，还要同时处理 opponent；若想完整表达，通常会出现 condition-like 或 state-derived params | 比 Judge 更复杂，但仍不需要 generator |
| `ptcg/cards/ASR/asr150roxanne.py` | `ASR150Roxanne` | 只有当对手 prize <= 3 时可用；自己手牌回 `left` 并洗牌，自己抽 6，对手抽 2 | 未来可能需要 `move_cards` + `draw_cards` + `shuffle_deck`，并在 resolver 层做严格前置检查 | 明确带条件 gating；当前 bridge 明确拒绝 `condition` 语义 | 即使不走 generator，也不该进入第一批 P0 |
| `ptcg/cards/ASC/lillies_determination.py` | `ASC192LilliesDetermination` | 手牌回 `left` 后洗牌，再根据 prize 是否恰好为 6 抽 6 或 8 | 未来可能需要 `move_cards` + `draw_cards` + `shuffle_deck` | draw count 含 prize 条件分支；当前 bridge 不接受条件型 op | 逻辑短，但不满足“无条件”的 P0 标准 |

## P2 暂不迁移卡 / 模式

| pattern | example files | reason |
| ------- | ------------- | ------ |
| generator / choice | `ptcg/cards/CRZ/energy_retrieval.py`, `ptcg/cards/PAL/bosss_orders.py` | 使用 `choose_card_actions` 和 `yield from reduce_choose_card_actions(...)`，当前 bridge 明确不支持 generator 和 choice |
| search deck | `ptcg/cards/SIT/capturing_aroma.py`, `ptcg/cards/OBF/obf189letterofencouragement.py` | 需要从 `left` 中检索特定子集并通常伴随 reveal/shuffle，已超出当前安全白名单 |
| coin flip | `ptcg/cards/SIT/capturing_aroma.py` | `flip_coin` 会把效果分支转成流程控制，不是当前 `StateOp` 范围 |
| reduce_attack_action | `ptcg/cards/TWM/twm25tealmaskogerponex.py`, `ptcg/cards/TEF/tef137cinccino.py` | 直接委托 `reduce_attack_action`，天然绑定战斗结算、伤害、击倒和 prize 流程 |
| damage / knockout | `ptcg/cards/TWM/twm25tealmaskogerponex.py`, `ptcg/cards/BRS/brs45raichuv.py` | 一旦进入攻击路径，就会触发 damage、KO、active replacement、prize 等复杂 reducer 逻辑 |
| attach energy | `ptcg/cards/PAR/par170professorsadasvitality.py`, `ptcg/cards/SVI/gardevoir_ex.py` | 涉及附能对象选择、区域移动和附着语义，当前 executor/bridge 均不支持 |
| evolve | `ptcg/cards/PAF/rare_candy.py` | 涉及 `EvolvePokemonAction`，并且和在场目标、回合限制、进化规则强耦合 |
| stadium | `ptcg/cards/BRS/collapsed_stadium.py` | 场地区域是 `State` 级对象，还牵涉 put/discard stadium、bench size 和连带弃牌流程 |
| on_knocked_out | `ptcg/cards/TEF/heavy_baton.py` | 通过 `on_knocked_out` hook 参与 KO 后流程，属于高耦合触发语义 |
| lost zone | `ptcg/cards/CRZ/lost_vacuum.py`, `ptcg/cards/LOR/lor58rotomv.py` | 直接写入 `CardPosition.LOSTZONE` 或依赖 lost zone 计数，当前阶段明确排除 |
| recursive delegation | `ptcg/cards/PAF/rare_candy.py` | `yield from evolved_card.reduce_action(EvolvePokemonAction(...), state)` 属于递归委托 legacy reducer，不适合作为第一批迁移对象 |
| optional / condition | `ptcg/cards/SIT/capturing_aroma.py`, `ptcg/cards/PAL/great_ball.py`, `ptcg/cards/ASR/asr150roxanne.py`, `ptcg/cards/ASC/lillies_determination.py` | 这些实现要么允许 0..1 选择、要么按 prize/coin flip/前置条件分支；当前 bridge 显式拒绝 `optional` 和 `condition` 语义 |

## 推荐第一张试迁移卡

推荐卡：

- `ptcg/cards/TWM/twm145carmine.py`

推荐原因：

- 它是本轮人工复核里最短、最纯粹的“固定顺序区域移动”型 Supporter
- 核心效果可以拆成非常稳定的三步：
  - `move_cards`：把 `Carmine` 自身从 `hand` 移到 `discard`
  - `discard_cards`：把剩余手牌全部从 `hand` 移到 `discard`
  - `draw_cards`：从 `left` 抽 5 张到 `hand`
- 不涉及 generator / choice
- 不涉及 search deck、coin flip、damage、knockout、attach energy、evolve、stadium、lost zone
- 不需要扩大当前 bridge 的安全白名单

需要哪些 `GameOp`：

- `move_cards`
- `discard_cards`
- `draw_cards`

是否需要新增 executor 能力：

- 不需要

是否需要新增 ZoneService 能力：

- 不需要

是否涉及 generator/choice：

- 不涉及

推荐如何写旁路测试：

- 在旁路测试里构造一个最小真实状态夹具，让当前玩家手牌中包含 `Carmine` 本体和若干其他手牌，`left` 至少有 5 张卡
- 直接调用 `resolve_ops(ctx)`，断言返回的 op 类型和顺序是：
  - 先弃置 supporter 自身
  - 再 `discard_cards(count="all")`
  - 最后 `draw_cards(count=5)`
- 再通过 `SemanticReducerBridge` 的旁路执行断言以下结果：
  - supporter 本体进入弃牌区
  - 其余旧手牌全部进入弃牌区
  - 5 张牌从 `left` 进入 `hand`
  - `fallback_required=False`
  - 返回事件只包含当前白名单 op 的结构化移动事件
- 第一版测试建议只比对区域变化和 bridge payload，不要求 bridge 旁路路径复现 `supporterPlayedTurn=True` 这类尚未建模的 legacy 标志位

## 下一阶段建议

下一阶段建议继续严格限制范围：

- 新开分支
- 只迁移 1 张 P0 候选卡
- 只新增 `resolve_ops`
- 不删除 legacy `reduce_action`
- 不接 `env.step`
- 只写旁路测试验证 `resolve_ops + bridge`

如果下一阶段发现真实卡的旁路测试必须同时表达 `supporterPlayedTurn` 之类非区域状态，再单独评估是否需要新增更小粒度的 state-side effect 建模；不要在同一轮里顺手扩大到 choice、shuffle 或条件语义。
