# Simple Supporter Side-channel Verification Template

> 文档日期：2026-06-14
> 版本：v1
> 状态：draft（Phase 7Y）
> 前置：Phase 7X（semantic draft golden summary）
> 后续：Phase 7Z（候选卡准入检查）

---

## 1. 适用范围

本模板**仅适用于** simple Supporter discard-and-draw 类型卡牌。

### 1.1 必须全部满足

| 条件 | 说明 |
|------|------|
| 类型为 Trainer / Supporter | `classification.trainer_subtype == "Supporter"` |
| `prompt_ready == true` | prompt preview 成功生成 |
| `draft_ready == true` | draft preview 成功生成 |
| 不需要 unsupported runtime op | 所有所需 op 均在当前 `_SUPPORTED_OPS` 中 |
| 效果可以表达为标准 4-step sequence | 见第 2 节 |

### 1.2 效果等价于如下 standard sequence

1. 使用的支援者自身进入弃牌区
2. 弃掉自己的手牌
3. 抽 N 张牌
4. 标记 supporter played

### 1.3 不涉及以下任何能力

| 排除条件 | 说明 |
|----------|------|
| choice | 不需要玩家选择（如选目标、选数量） |
| optional | 没有"可以……也可以……"分支 |
| conditional branch | 没有 if-then-else 条件逻辑 |
| search deck | 不涉及从牌库搜索指定卡牌 |
| both players | 不影响对方玩家区域 |
| prize count | 不读取或依赖奖赏卡数量 |
| deck bottom | 不涉及将卡牌放到牌库底部 |
| shuffle hidden zone | 不涉及洗牌操作 |
| opponent hand / deck 操作 | 不查看、不操作对方手牌或牌库 |
| coin flip / random | 不涉及掷硬币或随机操作 |
| reveal / look at hidden cards | 不涉及查看隐藏卡牌信息 |

**如果触及以上任何一条，本模板不适用，必须转入 manual review（见第 10 节）。**

---

## 2. 标准 semantic draft sequence

simple Supporter discard-and-draw 卡的标准 draft sequence：

| 序号 | op_type | 含义 | 关键参数 |
|------|---------|------|----------|
| 1 | `move_cards` | 将使用的 Supporter 自身从手牌移动到弃牌区 | `selector: this_card`, `source: self.hand`, `destination: self.discard` |
| 2 | `discard_cards` | 弃掉自己的全部手牌（效果文本中的"弃手牌"） | `count: "all"`, `actor: self`, `zone: hand` |
| 3 | `draw_cards` | 从牌库上方抽取 N 张卡牌 | `count: N`, `actor: self` |
| 4 | `mark_supporter_played` | 标记本回合已使用支援者 | `actor: self` |

### 2.1 关键约束

- **N 必须来自中文效果文本**：`draw_cards` 的 `count` 必须从效果文本中明确读出，不允许猜测或推算
- **draw count 不允许猜测**：如果文本为"抽X张"，则 X 必须是一个明确的数字
- **`discard_cards` 必须是自己的全部手牌**：`count` 必须为 `"all"`，不能为具体数字
- **`mark_supporter_played` 必须保留 legacy behavior**：对应`state.player.supporterPlayedTurn = True`
- **`move_cards` 表示使用的 Supporter 自身从手牌进入弃牌区**：区别于 discard_cards（弃掉其他手牌）

### 2.2 与 runtime op 的对应关系

draft preview 中的 op 使用**小写下划线命名**，runtime `resolve_ops` 使用 `OpType` 枚举：

| draft op_type | runtime OpType | 对应关系 |
|---------------|----------------|----------|
| `move_cards` | `OpType.MOVE_CARDS` | 1:1 |
| `discard_cards` | `OpType.DISCARD_CARDS` | 1:1 |
| `draw_cards` | `OpType.DRAW_CARDS` | 1:1 |
| `mark_supporter_played` | `OpType.MARK_SUPPORTER_PLAYED` | 1:1 |

当前 `_SUPPORTED_OPS` 恰好包含这 4 个 op：

```python
_SUPPORTED_OPS = {
    "move_cards",
    "discard_cards",
    "draw_cards",
    "mark_supporter_played",
}
```

---

## 3. 输入材料

后续单卡 side-channel PR 前必须准备以下材料：

| 序号 | 材料 | 来源 | 用途 |
|------|------|------|------|
| 1 | normalized card text / application preview | Phase 7D / 7E / 7F pipeline | 确认中文文本可信 |
| 2 | semantic extraction input preview | Phase 7R pipeline | 确认 card_context 完整 |
| 3 | prompt preview | Phase 7S pipeline | 确认 prompt_text 和 available_ops |
| 4 | semantic ops draft preview | Phase 7T pipeline | 确认 candidate_ops_sequence |
| 5 | golden test 或 alignment doc | Phase 7V / 7W | 固化为自动化测试 |
| 6 | 本地卡牌实现文件路径 | `ptcg/cards/SET/xxx.py` | 确认 resolve_ops 存在及对齐 |
| 7 | 现有 legacy 行为说明 | 卡牌实现中的 `reduce_action` 或 `execute` 方法 | 确认 sidechannel 行为一致 |
| 8 | 目标测试文件名 | 如 `tests/core/test_semantic_ops_xxx_sidechannel.py` | 命名规范 |
| 9 | 当前 runtime supported op inventory | `ptcg/data_sources/semantic_ops_draft.py` 中的 `_SUPPORTED_OPS` | 确认无缺失 op |

---

## 4. 准入检查清单

单卡进入 simple Supporter side-channel verification 前，逐项确认：

### 4.1 基础数据

- [ ] `card_key` 是否稳定（如 `SSH-178`、`TWM-145`）
- [ ] 本地卡牌文件是否存在（如 `ptcg/cards/SSH/ssh178professorsresearch.py`）
- [ ] 类型是否为 Trainer / Supporter（`classification.trainer_subtype == "Supporter"`）
- [ ] `classification.card_supertype == "Trainer"`
- [ ] `text`（效果文本）是否非空

### 4.2 pipeline 状态

- [ ] `prompt_ready` 是否为 `true`
- [ ] `draft_ready` 是否为 `true`
- [ ] `unsupported_or_needs_manual_review` 是否为 `false`
- [ ] `unsupported_reasons` 是否为空列表
- [ ] `candidate_ops_sequence` 是否已生成

### 4.3 op 能力匹配

- [ ] `candidate_ops_sequence` 中是否只使用 `_SUPPORTED_OPS` 中的 op
- [ ] 是否存在 `unsupported_or_needs_manual_review` 标记
- [ ] 是否确认不需要新 runtime op
- [ ] 所有 op 参数是否可被测试固定（无运行时决策依赖）

### 4.4 效果对齐

- [ ] `draw_cards` 的 `count` 是否明确（来自效果文本）
- [ ] draft sequence 是否可与 legacy `resolve_ops` 对齐
- [ ] draft sequence 是否可与 side-channel 行为对齐
- [ ] 是否已有或可新增 side-channel 测试
- [ ] `mark_supporter_played` 是否存在
- [ ] legacy `supporterPlayedTurn` 行为是否被保留

### 4.5 排除条件确认

- [ ] 不涉及 choice / optional / conditional branch
- [ ] 不涉及 search deck / shuffle / deck bottom
- [ ] 不涉及 both players / opponent
- [ ] 不涉及 prize count / coin flip
- [ ] 不涉及 reveal / look at hidden cards
- [ ] 不涉及 random / coin flip

---

## 5. side-channel PR 允许改哪些文件

### 5.1 允许修改

| 文件 | 范围 |
|------|------|
| 单张目标卡文件 | `ptcg/cards/SET/xxx.py` |
| 单张目标卡 side-channel 测试 | `tests/core/test_semantic_ops_xxx_sidechannel.py` |

### 5.2 谨慎允许（需在 PR 描述中说明理由）

| 文件 | 条件 |
|------|------|
| `tests/core/` shared helper | 重复代码已经明显变多（≥3 处相同 fixture/factory），可抽取 |
| `tests/data_sources/` golden test | 只补充对应卡的 golden case，不修改已有测试 |

### 5.3 绝对不允许

| 禁止修改 | 原因 |
|----------|------|
| `ptcg/core/*` | 核心模块变更风险高，需要单独审查 |
| `ptcg/core/ops.py`（semantic runtime） | 不允许扩展 runtime op |
| `ptcg/core/reducer.py` | 不允许修改降级逻辑 |
| `ptcg/core/envs.py` | 不允许修改环境步进 |
| `card_chinese_data.json` | 持久化数据，不在本流程范围 |
| `card_data_cache.json` | 持久化数据，不在本流程范围 |
| `data/normalized_card_text.json` | 正式 normalized JSON 不在此阶段生成 |
| `scripts/refetch_*.py` / pipeline 脚本 | 不在本流程范围 |
| 多张卡混在一个 PR | 每张卡独立 PR，便于审查和回滚 |
| 无关的格式化 / 清理 | 不扩大 diff 范围 |

---

## 6. resolve_ops 对齐要求

新增或检查 `resolve_ops` 时必须满足以下要求：

### 6.1 op 顺序

- op 顺序必须与 draft preview 的 `candidate_ops_sequence` 完全一致
- 标准顺序：`MOVE_CARDS → DISCARD_CARDS → DRAW_CARDS → MARK_SUPPORTER_PLAYED`

### 6.2 每个 op 的语义

| op | 要求 |
|-----|------|
| `MOVE_CARDS` | 处理使用的 Supporter 自身（`params: {"cards": self}`），source=hand, target=discard |
| `DISCARD_CARDS` | 处理自己的全部手牌（`params: {"count": "all"}`），actor=SELF, zone=hand |
| `DRAW_CARDS` | count 与效果文本一致，如 7 或 5，source=left, target=hand |
| `MARK_SUPPORTER_PLAYED` | 必须存在，actor=SELF，对应 legacy `supporterPlayedTurn` |

### 6.3 禁止事项

- 不加入 draft 中不存在的 runtime op
- 不用 generic `set_attr` 代替语义化 op
- 不把 playability note（如"先攻首回合可用"）塞进 resolve_ops effect sequence
- 不绕过 bridge / executor 当前支持范围
- 不添加 `order` 字段之外的排序依赖

### 6.4 resolve_ops 代码示例

标准 resolve_ops 模式（与 SSH-178 / TWM-145 一致）：

```python
def resolve_ops(self, ctx):
    return [
        GameOp(
            type=OpType.MOVE_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            order=1,
            source=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
            target=ZoneRef(PlayerSide.SELF, ZoneName.DISCARD),
            params={"cards": self},
        ),
        GameOp(
            type=OpType.DISCARD_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            order=2,
            source=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
            target=ZoneRef(PlayerSide.SELF, ZoneName.DISCARD),
            params={"count": "all"},
        ),
        GameOp(
            type=OpType.DRAW_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            order=3,
            source=ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
            target=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
            params={"count": N},  # N 来自效果文本
        ),
        GameOp(
            type=OpType.MARK_SUPPORTER_PLAYED,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            order=4,
        ),
    ]
```

需要替换的部分：`params={"count": N}` 中的 N。

---

## 7. side-channel 测试要求

### 7.1 测试必须覆盖

| 测试项 | 断言内容 |
|--------|----------|
| 支援者自身从手牌进入弃牌区 | `assert source_card in player.discard` |
| 使用后手牌被弃掉 | 原手牌全部在 discard，手牌只剩抽上来的 |
| 抽牌数量正确 | `assert len(player.hand) == N`（N 来自效果文本） |
| `supporterPlayedTurn` 被标记 | `assert player.supporterPlayedTurn is True` |
| side-channel 结果与 legacy 行为一致 | `result.fallback_required is False`, `result.used_semantic is True` |
| semantic bridge 接受该 op sequence | `result.op_results` 中所有 op 正确执行 |
| 不生成 unsupported op | op_types 全部在 `_SUPPORTED_OPS` 中 |
| 不影响其它玩家区域 | 对手区域无变化 |
| 不生成正式 semantic ops JSON | `must_not_emit_final_json == True` |
| 不需要 runtime 新能力 | 不依赖 `_SUPPORTED_OPS` 之外的 op |

### 7.2 测试文件命名规范

按照现有习惯：

```
tests/core/test_semantic_ops_<卡名英文小写>_sidechannel.py
```

示例：

- `test_semantic_ops_professors_research_sidechannel.py`（SSH-178）
- `test_semantic_ops_carmine_sidechannel.py`（TWM-145）

### 7.3 测试结构参考

参考现有 side-channel 测试的结构（以 SSH-178 的测试为例）：

```python
# 1. FakeCard / FakePlayer / FakeState dataclass fixtures
# 2. _make_*_fixture() 构建测试状态
# 3. test_*_resolver_returns_expected_sidechannel_ops() — 检查 resolve_ops
# 4. test_*_semantic_bridge_executes_sidechannel_zone_changes() — 检查 bridge
```

关键断言模式：

- `[op.type for op in ops] == [OpType.MOVE_CARDS, OpType.DISCARD_CARDS, OpType.DRAW_CARDS, OpType.MARK_SUPPORTER_PLAYED]`
- `ops[0].params["cards"] is source_card` — MOVE_CARDS 处理自身
- `ops[1].params == {"count": "all"}` — DISCARD_CARDS count=all
- `ops[2].params == {"count": N}` — DRAW_CARDS count=N
- `ops[3].params == {}` — MARK_SUPPORTER_PLAYED 无额外参数
- `result.used_semantic is True`
- `result.fallback_required is False`

---

## 8. legacy behavior 保留要求

### 8.1 必须保留的行为

| 行为 | 说明 |
|------|------|
| Supporter 使用后必须标记 `supporterPlayedTurn` | `player.supporterPlayedTurn = True` |
| legacy `reduce_action` / `execute` 行为应保持一致 | 已有实现的卡牌，side-channel 不应导致行为变化 |
| `UseSupporterAction` 仍然是入口 | 不新增 action 类型 |
| `get_actions` 逻辑不受影响 | 不修改可用条件判断 |

### 8.2 对齐原则

- draft preview 不能覆盖 legacy 行为
- 如果 legacy 和 draft preview **不一致**，必须停止并人工审查（见第 10 节）
- **不允许为了匹配 draft 而偷偷改 legacy 行为**
- 如果 legacy 行为正确但 draft 有误，应修正 draft 或标记 unsupported

### 8.3 legacy 检查清单

- [ ] `supporterPlayedTurn` 在 resolve_ops / reduce_action 中是否设置
- [ ] `get_actions` 中的 `supporterPlayedTurn` 检查是否保留
- [ ] 手牌弃牌逻辑是否一致（是否自行处理 each card）
- [ ] 抽牌逻辑是否一致（是否处理牌库不足）
- [ ] 支援者自身弃牌逻辑是否一致

---

## 9. 特殊说明处理

某些 simple Supporter 卡牌的效果文本中包含 timing / playability / condition 类说明。处理规则：

### 9.1 TWM-145 先攻首回合说明

TWM-145 Carmine 的效果文本：

> 这张卡牌，即使是先攻玩家的最初回合也可以使用。

处理方式：

- **属于 playability / timing note，不是 effect step**
- 只进入 `notes` / `risk_notes`
- 不生成 `first_turn` op
- 不生成 `play_condition` op
- 不生成 `allow_first_turn` op
- 不修改 `resolve_ops` effect sequence
- 不进入 runtime `candidate_ops_sequence`

golden test 中的验证方式：

```python
# candidate_ops_sequence 中不应出现 forbidden op types
forbidden = {"play_condition", "first_turn", "allow_first_turn", "custom"}
for op in result["candidate_ops_sequence"]:
    assert op["op_type"] not in forbidden
```

### 9.2 通用原则

效果文本中的非效果类说明（如 timing、playability、condition、restriction 等），在缺乏对应 runtime op 时：

1. 记录到 `risk_notes` 或 `special_notes`
2. **不**生成新的 semantic op
3. **不**弯曲现有 op 的语义去"勉强覆盖"
4. 当 runtime 扩展支持对应能力后，再重新评估

---

## 10. 必须停止并 manual review 的情况

以下任一情况发生时，**必须停止自动流程**，转入人工审查（manual review）：

### 10.1 效果类型排除

| 情况 | 说明 |
|------|------|
| both players | 涉及双方玩家 |
| opponent hand / deck | 操作对方手牌或牌库 |
| shuffle into deck | 洗入牌库 |
| deck bottom | 放到牌库底部 |
| prize count | 依赖奖赏卡数量 |
| conditional branch | 有 if-then-else 逻辑 |
| optional choice | 玩家可选择性执行 |
| search deck | 从牌库搜索 |
| reveal / look at hidden cards | 查看隐藏信息 |
| random | 随机操作 |
| coin flip | 掷硬币 |

### 10.2 数据/实现异常

| 情况 | 说明 |
|------|------|
| 需要新 op | 当前 `_SUPPORTED_OPS` 不足以表达效果 |
| legacy 行为不明确 | 无法从现有实现确定正确行为 |
| draw count 无法从文本确定 | 效果文本中没有明确的抽牌数量 |
| 本地卡牌文件不存在 | `ptcg/cards/SET/xxx.py` 不存在 |
| `card_key` 不稳定 | 编号/系列不确定 |
| `prompt_ready == false` | prompt preview 生成失败 |
| `draft_ready == false` | draft preview 生成失败 |
| `unsupported_or_needs_manual_review == true` | 自动分析认为需要人工 |

### 10.3 legacy 一致性异常

| 情况 | 说明 |
|------|------|
| draft 与 legacy `resolve_ops` 不一致 | 两者效果步骤不同 |
| draft 与 side-channel 行为不一致 | 测试暴露差异 |
| legacy 行为缺失 `supporterPlayedTurn` | 未标记支援者使用 |

### 10.4 停止后做什么

1. 在 PR 或 issue 中记录 `manual_review_needed` 标签
2. 描述具体阻塞原因
3. 建议需要的扩展（如新 op、新 runtime 能力）
4. 将卡牌列入 "pending review" 清单
5. **不要强行生成 candidate_ops_sequence**
6. **不要标记 draft_ready=true 绕过检查**

---

## 11. PR 模板

以下为 simple Supporter side-channel PR 的标准描述模板（中文）：

```markdown
## 这次做了什么

为 `<卡牌中文名> (<card_key>)` 新增 side-channel semantic ops 验证。

## 为什么要做

该卡为 simple Supporter discard-and-draw 类型（discard all + draw N），满足
Phase 7Y simple Supporter side-channel 验证模板的所有准入条件。

## 改了哪些文件

| 文件 | 变更 |
|------|------|
| `ptcg/cards/<SET>/<xxx>.py` | 新增/检查 resolve_ops |
| `tests/core/test_semantic_ops_<xxx>_sidechannel.py` | 新增 side-channel 测试 |

## semantic ops sequence

| 序号 | op_type | 参数 |
|------|---------|------|
| 1 | `MOVE_CARDS` | `cards: self`, hand -> discard |
| 2 | `DISCARD_CARDS` | `count: "all"` |
| 3 | `DRAW_CARDS` | `count: N` |
| 4 | `MARK_SUPPORTER_PLAYED` | `actor: SELF` |

## legacy behavior

- 该卡已有 reduce_action 实现，行为与 resolve_ops 一致
- supporterPlayedTurn 标记保留

## 测试覆盖

- [x] 支援者自身从手牌进入弃牌区
- [x] 使用后手牌被弃掉
- [x] 抽 N 张牌
- [x] supporterPlayedTurn 被标记
- [x] side-channel 结果与 legacy 行为一致
- [x] semantic bridge 接受该 op sequence
- [x] 不生成 unsupported op
- [x] 不影响其它玩家区域

## 安全边界

- [x] 未修改 `ptcg/core/`
- [x] 未修改 `card_chinese_data.json`
- [x] 未修改 `card_data_cache.json`
- [x] 未修改 `card_data_cache.json` / 正式 normalized JSON
- [x] 未修改 semantic runtime
- [x] 未修改 reducer / env.step
- [x] 未生成正式 semantic ops JSON

## 验证结果

```
$ uv run python -m pytest tests/core/test_semantic_ops_<xxx>_sidechannel.py -q
... passed
$ uv run python -m pytest tests/data_sources/test_xxx_semantic_draft_alignment_golden.py -q
... passed
```

## 下一步

- 后续 Phase：runtime 接入准备（需要有足够 golden cover 后）
- 不在此 PR 中生成正式 semantic ops JSON
```

### 11.1 PR 标题规范

```
<type>(ptcg-engine): <语义化的卡牌名> side-channel 验证
```

示例：

```
test(ptcg-engine): 博士的研究 (SSH-178) side-channel 验证
test(ptcg-engine): 丹瑜 (TWM-145) side-channel 验证
```

### 11.2 PR 描述必须说明

- PR 标题中文优先
- 是否新增 `resolve_ops`（还是只检查已有）
- 未修改 `ptcg/core`
- 未修改 JSON/cache
- 测试结果（pytest 输出）

---

## 12. 示例：SSH-178 Professor's Research / 博士的研究

| 项目 | 值 |
|------|-----|
| `card_key` | `SSH-178` |
| 卡名 | Professor's Research / 博士的研究 |
| 本地文件 | `ptcg/cards/SSH/ssh178professorsresearch.py` |
| 类型 | Trainer / Supporter |
| draw count | 7 |
| sequence | `move_cards → discard_cards → draw_cards → mark_supporter_played` |
| golden test | `tests/data_sources/test_ssh178_semantic_draft_alignment_golden.py` |
| side-channel test | `tests/core/test_semantic_ops_professors_research_sidechannel.py` |
| alignment doc | `docs/ssh178_semantic_draft_alignment.md` |
| unsupported runtime feature | 无 |

**关键点**：

- 已有完整 `resolve_ops`（4 个 op）
- 已有完整 `reduce_action`
- golden 与 side-channel 对齐
- 不涉及任何 unsupported 能力

---

## 13. 示例：TWM-145 Carmine / 丹瑜

| 项目 | 值 |
|------|-----|
| `card_key` | `TWM-145` |
| 卡名 | Carmine / 丹瑜 |
| 本地文件 | `ptcg/cards/TWM/twm145carmine.py` |
| 类型 | Trainer / Supporter |
| draw count | 5 |
| sequence | `move_cards → discard_cards → draw_cards → mark_supporter_played` |
| golden test | `tests/data_sources/test_twm145_semantic_draft_alignment_golden.py` |
| side-channel test | `tests/core/test_semantic_ops_carmine_sidechannel.py` |
| special notes | 先攻首回合可使用 — 仅记录为 notes/risk_notes，不生成新 op |
| unsupported runtime feature | 无 |

**关键点**：

- 已有完整 `resolve_ops`（4 个 op）
- 已有完整 `reduce_action`
- 先攻首回合说明正确归入 notes，未生成额外 op
- golden 与 side-channel 对齐

---

## 14. 下一阶段建议

### Phase 7Z：下一张 simple Supporter 候选卡准入检查

建议流程：

1. **选择候选卡**：从已知 Trainer/Supporter 卡牌中选择一张尚未进入 side-channel 的候选卡
2. **运行 refetch / application / input / prompt / draft preview pipeline**：对候选卡生成完整的 preview 链
3. **对照本模板准入检查清单**（第 4 节）逐项判断
4. **不满足准入条件 → manual review**：标记 `manual_review_needed`，不进入 side-channel PR
5. **满足准入条件 → golden test + side-channel 验证**

推荐候选卡方向：

- 其他系列中与 SSH-178 效果相同的 Professor's Research 变体（如 SVI-189 等）
- 确认存在本地卡牌文件、中文文本可信、效果仅涉及 discard-all + draw-N

### Phase 7Z 产出

- `docs/<新卡>_semantic_draft_alignment.md`（对齐文档）
- `tests/data_sources/test_<新卡>_semantic_draft_alignment_golden.py`（golden test）

> **注意**：Phase 7Y + Phase 7Z 完成后统一 push，创建一个 docs PR。
