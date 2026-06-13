# Semantic Draft Golden Summary

> 文档日期：2026-06-14
> 审查阶段：Phase 7X
> 前置阶段：Phase 7V (SSH-178 golden test)、Phase 7W (TWM-145 golden test)

---

## 1. 当前阶段目标

当前 semantic pipeline 已从以下阶段推进到双卡 golden case 阶段：

```
normalized card text (Phase 7D)
  -> refetch preview (Phase 7E)
    -> application preview (Phase 7F)
      -> semantic extraction input preview (Phase 7R)
        -> prompt preview (Phase 7S)
          -> semantic ops draft preview (Phase 7T)
            -> alignment document (Phase 7U)
              -> golden test (Phase 7V / 7W)
                -> summary report (Phase 7X, 本文档)
```

关键约束（当前 golden 仍然在此边界内）：

- 当前 golden 仍然是 **draft preview 层**，不是正式 semantic ops JSON
- **不可被 runtime 直接加载**
- **不直接修改 card implementation**（不修改 `ptcg/cards/`、`ptcg/core/`）
- **不生成 `semantic_ops.json`**、`data/normalized_card_text.json`
- **不修改 `card_chinese_data.json`**、`card_data_cache.json`
- **不调用 LLM**、**不依赖网络**

---

## 2. 当前已固定的 golden cards

| card_key | 卡名 | 类型 | 预期 sequence | draw count | special notes | status |
|----------|------|------|---------------|------------|---------------|--------|
| SSH-178 | Professor's Research / 博士的研究 | Trainer / Supporter | move_cards -> discard_cards -> draw_cards -> mark_supporter_played | 7 | 无 | golden test exists (`test_ssh178_semantic_draft_alignment_golden.py`) |
| TWM-145 | Carmine / 丹瑜 | Trainer / Supporter | move_cards -> discard_cards -> draw_cards -> mark_supporter_played | 5 | usable_on_first_turn_if_going_first（先攻玩家的最初回合也可以使用） | golden test exists (`test_twm145_semantic_draft_alignment_golden.py`) |

两张卡共享相同的 core sequence 结构，唯一的差异是：

- `draw_cards` 的 count 参数（SSH-178=7，TWM-145=5）
- TWM-145 有一条 special note（先攻首回合可用），但不产生新的 op

---

## 3. Golden sequence 标准

simple Supporter discard-and-draw 卡的标准 sequence：

| 序号 | op_type | 含义 | 关键参数 |
|------|---------|------|----------|
| 1 | `move_cards` | 将使用的 Supporter 自身从手牌移动到弃牌区 | `selector: this_card`, `source: self.hand`, `destination: self.discard` |
| 2 | `discard_cards` | 弃掉自己的全部手牌（效果文本中的弃手牌） | `count: "all"`, `actor: self`, `zone: hand` |
| 3 | `draw_cards` | 从牌库上方抽取指定数量卡牌 | `count: N`（N 取决于具体卡牌） |
| 4 | `mark_supporter_played` | 标记本回合已使用支援者（保留 legacy `supporterPlayedTurn` 行为） | `actor: self` |

这 4 个 op 与当前 runtime 支持的 op 清单完全一致：

```
_SUPPORTED_OPS = {
    "move_cards",
    "discard_cards",
    "draw_cards",
    "mark_supporter_played",
}
```

注意：draft preview 中的 op 使用**小写下划线命名**（与 `semantic_ops_draft.py` 中的 `op_type` 字段一致），而 runtime `resolve_ops` 中使用的是 `ptcg.core.ops.OpType` 枚举（如 `OpType.MOVE_CARDS`）。二者语义等价，但格式不同——golden test 固定的是 draft preview 层的命名。

---

## 4. Golden test 必须固定的字段

golden test 必须至少断言以下字段和条件：

### 基础元数据

- `card_key` — 必须与目标卡一致
- `draft_ready` — 必须为 `True`
- `unsupported_or_needs_manual_review` — 必须为 `False`
- `must_not_emit_final_json` — 必须为 `True`

### meta 字段

- `meta.writes_semantic_ops_json` — 必须为 `False`
- `meta.writes_cards` — 必须为 `False`
- `meta.writes_core` — 必须为 `False`
- `meta.calls_llm` — 必须为 `False`
- `meta.network_enabled` — 必须为 `False`
- `meta.dry_run` — 必须为 `True`

### candidate_ops_sequence

- 长度为 4
- `op_type` 顺序严格等于预期 golden sequence
- `discard_cards` 的 `count` 为 `"all"`
- `draw_cards` 的 `count` 为具体卡牌的固定值（SSH-178=7, TWM-145=5）
- `mark_supporter_played` 的 `actor` 为 `"self"`
- 每个 op 都有 `purpose` 字段

### 禁止出现的字段

输出中不应包含任何 runtime-loadable 字段：

- `semantic_ops`
- `final_ops`
- `runtime_loadable_ops`
- `resolve_ops_code`
- `card_patch`
- `ops`

### 原始 JSON 不变

- `card_chinese_data.json` 测试前后 SHA-256 一致
- `card_data_cache.json` 测试前后 SHA-256 一致

---

## 5. 特殊说明处理规则

### TWM-145 先攻首回合说明

TWM-145 Carmine 的中文效果文本包含：

> 这张卡牌，即使是先攻玩家的最初回合也可以使用。

处理方式：

- 属于 **playability / timing note**，不是 effect step
- 当前 draft preview 只保留为 **notes / risk_notes**
- 不生成 `first_turn` op
- 不生成 `play_condition` op
- 不生成 `allow_first_turn` op
- 不生成任何 `custom` op
- 不修改 `resolve_ops`
- 不进入 runtime sequence

验证方式（在 golden test 中）：

```python
risk_notes = result.get("risk_notes", [])
assert any(
    "usable_on_first_turn" in note or "先攻" in note
    for note in risk_notes
)
# candidate_ops_sequence 中不应出现 forbidden op types
forbidden = {"play_condition", "first_turn", "allow_first_turn", "custom"}
for op in result["candidate_ops_sequence"]:
    assert op["op_type"] not in forbidden
```

### 通用原则

效果文本中的 timing / playability / condition 类说明（如"即使是先攻玩家的最初回合"、"如果自己的场上有X"等），在缺乏对应 runtime op 时：

1. 记录到 `risk_notes` 或 `special_notes`
2. **不**生成新的 semantic op
3. **不**弯曲现有 op 的语义去"勉强覆盖"
4. 当 runtime 扩展支持对应能力后，再重新评估

---

## 6. 当前不能进入 golden sequence 的卡

以下卡牌已在代码中标记为 `unsupported_or_needs_manual_review=True`，**不应强行生成 `candidate_ops_sequence`**：

| card_key | 卡名 | 不支持原因 |
|----------|------|-----------|
| PAL-185 | Iono | 涉及 both_players、hand_to_deck_bottom、prize_count_conditional |
| FLI-108 | Judge | 涉及 both_players、shuffle_hand_into_deck |
| ASR-150 | Roxanne | 涉及 both_players、conditional_prize_count、hand_back_to_deck |

这些卡牌不能进入 golden sequence 的具体原因：

- **both_players**：当前 runtime 主要针对单玩家操作设计，缺少双方玩家统一处理语义
- **shuffle / deck bottom**：当前缺少 shuffle 语义和 deck bottom 定位
- **prize count / conditional**：当前缺少条件分支 op（如 `if prize_count >= N then ...`）
- **choice / optional**：缺少玩家选择语义

如果强行生成 candidate_ops_sequence：

- 会遗漏关键效果步骤
- 会导致 resolve_ops 与实际效果不一致
- 会破坏 golden test 的可信度
- 应在 `draft_ready=False` 下标记 `unsupported_or_needs_manual_review=True`

---

## 7. 从 draft preview 到 golden test 的准入条件

一张卡要进入 golden test，必须满足以下**全部**条件：

| 条件 | 说明 |
|------|------|
| `prompt_ready=True` | prompt preview 成功生成 |
| `draft_ready=True` | draft preview 成功生成 |
| `unsupported_or_needs_manual_review=False` | 未标记为需要人工审查 |
| 所需 op 全部在 `_SUPPORTED_OPS` 中 | runtime op inventory 覆盖所有操作 |
| draft sequence 可与 legacy `resolve_ops` 对齐 | 现有实现与 draft 一致 |
| draft sequence 可与 side-channel 行为对齐 | side-channel 测试通过 |
| draw/discard/move/mark 参数可被测试固定 | 所有参数是确定值（非运行时决策） |
| 不依赖未支持能力 | 无 choice / optional / conditional / search deck / both players / shuffle / deck bottom / prize count / coin flip |

**反例**：如果一张卡：

- 虽然可以生成 4 个 op，但实际效果还包含 search deck 或 conditional 逻辑
- 虽然 prompt_ready 为 true，但 normalized text 质量不可信
- 虽然有 `resolve_ops`，但 side-channel 测试尚未覆盖

则不应进入 golden test。

---

## 8. 后续新卡流程

推荐新卡进入 semantic draft golden 的完整流程：

```
1. refetch preview
   - 确认中文文本可用
   - 确认 normalized text 质量

2. application preview
   - 确认 patch 不会覆盖已有可信数据
   - 确认不引入新错误

3. semantic extraction input preview
   - 确认 card_context 完整
   - 确认 classification 正确

4. prompt preview
   - 确认 prompt_text 质量
   - 确认 available_ops 正确

5. semantic ops draft preview
   - 确认 draft_ready
   - 确认无 unsupported 标记

6. alignment review document
   - 手动对齐 draft sequence 与 resolve_ops
   - 逐项对比参数

7. golden test
   - 固定 sequence
   - 固定参数
   - 固定 notes
   - 验证原始 JSON 不变

8. side-channel implementation or verification PR
   - 如果卡牌已有 resolve_ops -> side-channel 验证 PR
   - 如果卡牌尚无 resolve_ops -> side-channel 实现 PR

9. runtime integration
   - 仅当有足够 golden coverage 后
   - 生成正式 semantic_ops.json
   - 接入 env.step
```

每一步都应**单独 PR**，避免 stacked PR（除非前一步尚未合并且后一步依赖前一步的输出文件）。

---

## 9. 安全边界

golden test 和 draft preview pipeline 的安全边界，必须严格遵守：

### 禁止事项

| 禁止 | 原因 |
|------|------|
| 把 draft preview 当成正式 semantic ops JSON | draft 是审查辅助工具，不是 runtime 可执行数据 |
| 生成 runtime-loadable ops 文件 | 尚未经过充分人工审查和 runtime 回归 |
| 让 LLM 直接修改 `ptcg/cards/` | 卡牌实现需要保证确定性、可测试性、可审查性 |
| 让 LLM 直接修改 `ptcg/core/` | core 模块修改风险高，需要人工设计 |
| 绕过 golden test 直接进入实现 | golden test 是对齐和回归的安全网 |
| 覆盖原始 JSON 文件 | `card_chinese_data.json` 和 `card_data_cache.json` 是持久化数据，修改需要单独审核 |
| preview 输出进入仓库 | 仓库只保留代码和测试，preview JSON 应留在仓库外（如 `%TEMP%`） |

### 允许事项

| 允许 | 范围 |
|------|------|
| golden test 文件 | `tests/data_sources/test_*_semantic_draft_alignment_golden.py` |
| alignment review 文档 | `docs/*_semantic_draft_alignment.md` |
| summary 文档 | `docs/semantic_draft_golden_summary.md` |
| draft preview 代码 | `ptcg/data_sources/semantic_ops_draft.py`（不含 LLM / network 调用） |
| draft preview 测试 | `tests/data_sources/test_build_semantic_ops_draft.py` |

---

## 10. 下一阶段建议

建议 Phase 7Y 从以下方向中选择：

### 方向 A：simple Supporter draft -> side-channel verification 模板

为 simple Supporter 类卡牌（discard-all + draw-N + mark）制定一个标准化的验证模板，使得后续新卡（如其他系列的 Professor's Research 变体）可以直接套用模板快速完成 side-channel 验证。

### 方向 B：SSH-178 / TWM-145 统一 alignment report test

创建一个跨 golden case 的综合性测试，确保两张卡不会互相干扰、共享逻辑不会漂移。

### 方向 C：暂不扩展

暂不扩展到 Iono / Judge / Roxanne，除非先扩展 runtime op inventory（增加 shuffle、deck bottom、both players、conditional 等能力）。

### 推荐

推荐先执行**方向 A**，将当前两张 simple Supporter 的成功经验固化为可复用的模板，确保后续同类型卡牌可以快速进入 golden 流程。
