# SSH-178 semantic ops draft 对齐审查报告

> 审查日期：2026-06-13
> 审查阶段：Phase 7U
> 审查范围：SSH-178 Professor's Research / 博士的研究

---

## 1. 审查对象

| 项目 | 值 |
|------|-----|
| card_key | SSH-178 |
| 卡名 | Professor's Research / 博士的研究 |
| 卡牌类型 | Trainer / Supporter |
| 本地实现 | `ptcg/cards/SSH/ssh178professorsresearch.py` |
| 类名 | `SSH178ProfessorsResearch` |
| 继承 | `SupporterCard` |

### 使用的 draft preview 文件

本审查使用的 draft preview 通过完整 Phase 7R → 7S → 7T 链路生成，输出到仓库外临时目录（`%TEMP%\ptcg-refetch-preview\`），文件名：

- `phase7u_ssh178_refetch_preview.json`
- `phase7u_ssh178_application_preview.json`
- `phase7u_ssh178_input_preview.json`
- `phase7u_ssh178_prompt_preview.json`
- `phase7u_ssh178_ops_draft_preview.json`

---

## 2. 中文效果文本

来自现有卡牌实现 `SSH178ProfessorsResearch.text`：

> 将自己的所有手牌丢弃，然后从牌库上方抽取7张。

draft preview 生成的 `effect_summary`：

> 将自己的手牌全部丢弃，然后抽 7 张牌，并标记本回合已使用支援者。

二者语义等价，draft 额外包含了 `mark_supporter_played` 的描述（因为现有 `text` 字段不显式写支援者标记，但 resolve_ops 中包含此步骤）。

---

## 3. Draft preview 候选 ops

从 `phase7u_ssh178_ops_draft_preview.json` 中提取 `candidate_ops_sequence`：

| 序号 | op_type | purpose | draft_args |
|------|---------|---------|------------|
| 1 | `move_cards` | 将使用的 Supporter 自身从手牌移动到弃牌区 | `source: self.hand`, `destination: self.discard`, `selector: this_card` |
| 2 | `discard_cards` | 弃掉自己的全部手牌 | `actor: self`, `zone: hand`, `count: all` |
| 3 | `draw_cards` | 抽 7 张牌 | `actor: self`, `count: 7` |
| 4 | `mark_supporter_played` | 标记本回合已使用支援者 | `actor: self` |

关键元数据：

- `draft_ready`: `true`
- `unsupported_or_needs_manual_review`: `false`
- `calls_llm`: `false`
- `must_not_emit_final_json`: `true`

---

## 4. 现有 resolve_ops 对齐结果

现有实现来自 `ptcg/cards/SSH/ssh178professorsresearch.py` 第 31-56 行的 `resolve_ops()` 方法：

| 序号 | OpType | actor | source | target | params |
|------|--------|-------|--------|--------|--------|
| 1 | `MOVE_CARDS` | SELF | hand | discard | `{"cards": self}` |
| 2 | `DISCARD_CARDS` | SELF | hand | discard | `{"count": "all"}` |
| 3 | `DRAW_CARDS` | SELF | left | hand | `{"count": 7}` |
| 4 | `MARK_SUPPORTER_PLAYED` | SELF | - | - | `{}` |

### 逐项对齐

| 检查项 | draft preview | resolve_ops | 是否对齐 |
|--------|---------------|-------------|----------|
| move_cards 是否存在 | 是（op 1） | 是（op 1） | 对齐 |
| discard_cards 是否存在 | 是（op 2） | 是（op 2） | 对齐 |
| draw_cards count | **7** | **7** | 对齐 |
| mark_supporter_played 是否存在 | 是（op 4） | 是（op 4） | 对齐 |
| 操作顺序 | move → discard → draw(7) → mark | MOVE → DISCARD → DRAW(7) → MARK | 对齐 |
| 总 op 数量 | 4 | 4 | 对齐 |

**结论：draft preview 的 candidate_ops_sequence 与现有 resolve_ops 完全一致。**

---

## 5. Side-channel 测试对齐结果

已有测试：`tests/core/test_semantic_ops_professors_research_sidechannel.py`

### 测试 1：`test_professors_research_resolver_returns_expected_sidechannel_ops`

验证 resolver 返回的 ops 顺序与类型：

```python
assert [op.type for op in ops] == [
    OpType.MOVE_CARDS,
    OpType.DISCARD_CARDS,
    OpType.DRAW_CARDS,
    OpType.MARK_SUPPORTER_PLAYED,
]
assert ops[0].params["cards"] is professors_research
assert ops[1].params == {"count": "all"}
assert ops[2].params == {"count": 7}
assert ops[3].params == {}
```

这与 draft preview 的 candidate_ops_sequence 完全一致。

### 测试 2：`test_professors_research_semantic_bridge_executes_sidechannel_zone_changes`

验证桥接器执行后的区域变化：

- `player.supporterPlayedTurn is True`
- 所有手牌（含 Supporter 自身）进入 `player.discard`
- `player.hand` 包含 deck 前 7 张
- `player.left` 剩余 1 张（原 8 张）
- legacy behavior 与 side-channel 行为一致

**结论：draft preview 的 ops 顺序与 side-channel 测试期望完全对齐。**

---

## 6. Runtime 支持状态

### 当前 bridge 支持

`ptcg/core/ops/bridge.py` (`SemanticReducerBridge._SUPPORTED_OP_TYPES`)：

```python
_SUPPORTED_OP_TYPES = {
    OpType.MARK_SUPPORTER_PLAYED,
    OpType.MOVE_CARDS,
    OpType.DRAW_CARDS,
    OpType.DISCARD_CARDS,
}
```

SSH-178 需要的全部 4 种 op 均在支持列表中。

### 当前 executor 支持

`ptcg/core/ops/executor.py` (`OperationExecutor.execute_op`)：

| OpType | 实现方法 |
|--------|----------|
| `MOVE_CARDS` | `_execute_move_cards` |
| `DISCARD_CARDS` | `_execute_discard_cards` |
| `DRAW_CARDS` | `_execute_draw_cards` |
| `MARK_SUPPORTER_PLAYED` | `_execute_mark_supporter_played` |

全部 4 种 op 均有完整实现，且已被 `test_operation_executor.py` 和 `test_semantic_reducer_bridge.py` 覆盖。

### 覆盖的测试文件

| 测试文件 | 覆盖范围 |
|----------|----------|
| `tests/core/test_operation_executor.py` | executor 单元测试（move/draw/discard/supporter） |
| `tests/core/test_semantic_reducer_bridge.py` | bridge 集成测试 |
| `tests/core/test_semantic_ops_professors_research_sidechannel.py` | SSH-178 专有侧信道测试 |
| `tests/data_sources/test_build_semantic_ops_draft.py` | draft preview 生成测试 |

**结论：SSH-178 需要的全部 op 均有 runtime 支持，bridge 和 executor 均就绪。**

---

## 7. 风险与限制

| 风险项 | 是否涉及 | 说明 |
|--------|----------|------|
| choice（玩家选择） | 否 | 本卡无交互选择 |
| optional（可选效果） | 否 | 效果为强制触发 |
| conditional branch（条件分支） | 否 | 无条件分支 |
| search deck（搜索牌库） | 否 | 无搜索操作 |
| both players（双方玩家） | 否 | 只影响当前玩家 |
| prize count（奖赏卡数量） | 否 | 无奖赏卡条件 |
| deck bottom（牌库底部） | 否 | 无底部操作 |
| coin flip（硬币翻转） | 否 | 无随机判定 |

**SSH-178 是最简单的 Supporter 效果模式：无条件全弃 + 固定数量抽牌 + 标记。因此适合作为第一张 draft alignment golden case。**

---

## 8. 结论

### 对齐结果：**全部通过**

1. **draft preview candidate ops 与 resolve_ops 一致**：4 种 op 类型、顺序、参数均匹配
2. **ops 顺序一致**：move_cards → discard_cards → draw_cards(7) → mark_supporter_played
3. **draw count 一致**：均为 7
4. **mark_supporter_played 存在**：draft 和 resolve 均有此 op
5. **legacy behavior 保留**：`reduce_action` 方法仍然存在，side-channel 测试确认 legacy 和 semantic 行为一致
6. **runtime 支持完整**：bridge 和 executor 均支持全部 4 种 op
7. **无风险项**：本卡不涉及 choice / optional / conditional / search / both players / prize count / deck bottom

### 建议

- **可以进入 Phase 7V**：将 SSH-178 draft preview 固化为单卡审核 fixture / golden report test
- **不建议直接修改卡牌实现**：SSH-178 已有 `resolve_ops` 和 `reduce_action` 双路径实现，并由 side-channel 测试覆盖，当前没有修改卡牌文件的必要性

---

## 附录：审查文件清单

| 文件 | 角色 |
|------|------|
| `ptcg/data_sources/semantic_ops_draft.py` | draft preview 核心逻辑 |
| `scripts/build_semantic_ops_draft.py` | draft preview CLI 入口 |
| `tests/data_sources/test_build_semantic_ops_draft.py` | draft 测试 |
| `ptcg/cards/SSH/ssh178professorsresearch.py` | SSH-178 卡牌实现 |
| `tests/core/test_semantic_ops_professors_research_sidechannel.py` | 侧信道测试 |
| `ptcg/core/ops/types.py` | OpType / GameOp 定义 |
| `ptcg/core/ops/bridge.py` | SemanticReducerBridge |
| `ptcg/core/ops/executor.py` | OperationExecutor |
| `tests/core/test_operation_executor.py` | executor 测试 |
| `tests/core/test_semantic_reducer_bridge.py` | bridge 测试 |
