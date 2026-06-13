# Simple Supporter Next Candidate Admission Report

> 文档日期：2026-06-14
> 阶段：Phase 7Z
> 前置：Phase 7Y（simple Supporter side-channel 验证模板）
> 状态：完成

---

## 1. 背景

### 1.1 本报告基于

- Phase 7Y 模板：`docs/simple_supporter_sidechannel_verification_template.md`
- 当前 semantic draft golden summary：`docs/semantic_draft_golden_summary.md`

### 1.2 当前已有的 simple Supporter golden cards

| card_key | 卡名 | draw count | 状态 |
|----------|------|------------|------|
| SSH-178 | Professor's Research / 博士的研究 | 7 | golden test + side-channel test |
| TWM-145 | Carmine / 丹瑜 | 5 | golden test + side-channel test |

二者共享 standard sequence：

```
move_cards → discard_cards(count=all) → draw_cards(count=N) → mark_supporter_played(actor=self)
```

### 1.3 当前已知不能进入 simple sequence 的 Supporter

| card_key | 卡名 | 阻挡原因 |
|----------|------|----------|
| PAL-185 | Iono | both_players, hand_to_deck_bottom, prize_count_conditional |
| FLI-108 | Judge | both_players, shuffle_hand_into_deck |
| ASR-150 | Roxanne | both_players, conditional_prize_count, hand_back_to_deck |

---

## 2. 候选计划摘要

### 2.1 dry-run plan 前 30 个候选

通过 `scripts/refetch_card_text_preview.py --limit 30`（dry-run，network=False），输出在仓库外 `%TEMP%\ptcg-refetch-preview\phase7z_candidate_plan_preview.txt`。

前 30 个候选 card_key：

| rank | card_key | can_refetch | blocking_issues | initial note |
|------|----------|-------------|-----------------|--------------|
| 1 | ASC-189 | network_disabled | [] | 未联网，分类未知 |
| 2 | ASR-136 | network_disabled | [] | 未联网，分类未知 |
| 3 | ASR-141 | network_disabled | [] | 未联网，分类未知 |
| 4 | ASR-146 | network_disabled | [] | 未联网，分类未知 |
| 5 | ASR-147 | network_disabled | [] | Irida — search deck + reveal + shuffle |
| 6 | ASR-150 | network_disabled | [] | Roxanne — 已知 complex |
| 7 | ASR-152 | network_disabled | [] | 未联网，分类未知 |
| 8 | ASR-154 | network_disabled | [] | 未联网，分类未知 |
| 9 | ASR-156 | network_disabled | [] | 未联网，分类未知 |
| 10 | BRS-137 | network_disabled | [] | 未联网，分类未知 |
| 11 | CES-129 | network_disabled | [] | 未联网，分类未知 |
| 12 | CIN-091 | network_disabled | [] | 未联网，分类未知 |
| 13 | CRZ-127 | network_disabled | [] | 未联网，分类未知 |
| 14 | CRZ-135 | network_disabled | [] | 未联网，分类未知 |
| 15 | FLI-108 | network_disabled | [] | Judge — 已知 complex |
| 16 | GRI-122 | network_disabled | [] | 未联网，分类未知 |
| 17 | LOR-167 | network_disabled | [] | Thorton — search deck + switch + shuffle |
| 18 | MEW-165 | network_disabled | [] | 未联网，分类未知 |
| 19 | OBF-186 | network_disabled | [] | 未联网，分类未知 |
| 20 | OBF-189 | network_disabled | [] | 未联网，分类未知 |
| 21 | OBF-196 | network_disabled | [] | 未联网，分类未知 |
| 22 | PAF-079 | network_disabled | [] | 未联网，分类未知 |
| 23 | PAF-081 | network_disabled | [] | 未联网，分类未知 |
| 24 | PAL-171 | network_disabled | [] | 未联网，分类未知 |
| 25 | PAL-173 | network_disabled | [] | 未联网，分类未知 |
| 26 | PAL-183 | network_disabled | [] | 未联网，分类未知 |
| 27 | PAL-185 | network_disabled | [] | Iono — 已知 complex |
| 28 | PAL-188 | network_disabled | [] | 未联网，分类未知 |
| 29 | PAL-189 | network_disabled | [] | 未联网，分类未知 |
| 30 | PAL-265 | network_disabled | [] | Boss's Orders — opponent switch |

### 2.2 前 30 个中的 Trainer / Supporter 卡

检查所有本地卡牌文件（`ptcg/cards/**/*.py`），在前 30 个候选中识别出以下 Supporter：

| card_key | 文件 | 卡名 | 效果简述 | 是否可能 simple |
|----------|------|------|----------|-----------------|
| ASR-147 | `ptcg/cards/ASR/asr147irida.py` | 珠贝 / Irida | search deck + reveal + shuffle | 否（search deck） |
| **ASR-150** | `ptcg/cards/ASR/asr150roxanne.py` | 大叶 / Roxanne | both players return hand to deck + draw based on prize count | 否（both_players + conditional） |
| FLI-108 | `ptcg/cards/FLI/fli108judge.py` | 赤日 / Judge | both players shuffle hand into deck + draw 4 | 否（both_players + shuffle） |
| LOR-167 | `ptcg/cards/LOR/lor167thorton.py` | 捩木 / Thorton | search deck + switch + shuffle | 否（search deck + switch） |
| PAL-185 | `ptcg/cards/PAL/pal185iono.py` | 清丽 / Iono | both players put hand to deck bottom + draw based on prize count | 否（both_players + prize_count） |
| PAL-265 | `ptcg/cards/PAL/bosss_orders.py` | 老大的指令 / Boss's Orders | opponent bench switch | 否（opponent 操作） |

**结论：前 30 个候选中没有任何一个 simple discard-and-draw Supporter。**

---

## 3. 本阶段选择的候选卡

### 基本信息

| 项目 | 值 |
|------|-----|
| **selected card_key** | **ASR-150** |
| 卡名 | Roxanne / 大叶 |
| 类型 | Trainer / Supporter |
| 本地文件 | `ptcg/cards/ASR/asr150roxanne.py` |
| 已有 golden | 否（已在 golden summary 第 6 节中标记为 unsupported） |
| 已有 side-channel test | 否 |
| can_refetch | true（联网 refetch 成功） |
| blocking_issues | [] |

### 选择原因

ASR-150 是 Phase 7X golden summary 中明确标记为 `unsupported_or_needs_manual_review=True` 的卡牌。选择它的目的是：

1. **验证 Phase 7Y 模板的拦截能力**：确认模板能正确识别并阻止不满足准入条件的卡牌进入 simple side-channel verification
2. **记录完整 preview 链路输出**：展示从 refetch 到 draft preview 的完整流程，为后续类似卡牌提供参考
3. **示范 manual review 的触发条件**：both_players + conditional + hand_back_to_deck 是典型的复杂 Supporter 场景

**注意：选择 ASR-150 不是为了强行通过 simple sequence，而是为了验证模板能正确拦住不合格候选。**

---

## 4. Preview 链路结果

所有 preview 输出文件均位于仓库外 `%TEMP%\ptcg-refetch-preview\`。

| step | result | output file | notes |
|------|--------|-------------|-------|
| refetch preview | **pass** | `phase7z_asr150_refetch_preview.json` | patch: text, classification |
| application preview | **pass** | `phase7z_asr150_application_preview.json` | applied_fields=5, skipped=0 |
| semantic extraction input preview | **pass** | `phase7z_asr150_input_preview.json` | task=supporter_effect_to_semantic_ops, ready=true |
| prompt preview | **pass** | `phase7z_asr150_prompt_preview.json` | prompt_ready=true, prompt_text=1411 chars |
| semantic ops draft preview | **pass** | `phase7z_asr150_draft_preview.json` | draft_ready=**false**, manual_review=**true** |

### 详细说明

#### refetch preview

```json
{
  "card_key": "ASR-150",
  "patch": ["text", "classification"],
  "can_refetch": true,
  "blocking_issues": []
}
```

联网 refetch 成功，获取到中文效果文本和分类信息。

#### application preview

```json
{
  "card_key": "ASR-150",
  "applied": true,
  "applied_fields": 5,
  "skipped_fields": 0,
  "errors": 0
}
```

5 个字段成功应用（text, classification 相关），无错误。

#### prompt preview

- `prompt_ready`: true
- `available_ops`: `move_cards, discard_cards, draw_cards, mark_supporter_played`
- `prompt_text`: 1411 chars（包含完整的 card_context、identity、classification、normalized_text）
- `needs_manual_review`: false（在 prompt 层面未标记，但在 draft 层面触发）

#### semantic ops draft preview

```json
{
  "card_key": "ASR-150",
  "draft_ready": false,
  "unsupported_or_needs_manual_review": true,
  "unsupported_reasons": [
    "conditional_or_both_players_unsupported"
  ],
  "effect_summary": "Roxanne - 当前 runtime 不支持（both_players, conditional_prize_count, hand_back_to_deck）",
  "candidate_ops_sequence": [],
  "risk_notes": [
    "需要 runtime 支持: both_players, conditional_prize_count, hand_back_to_deck"
  ],
  "must_not_emit_final_json": true
}
```

**关键发现**：虽然 prompt preview 层面看起来正常（prompt_ready=true, available_ops 包含 4 个标准 op），但 draft 层正确识别到效果文本中包含 beyond-simple 的操作：

- `both_players` — 双玩家操作
- `conditional_prize_count` — 基于奖赏卡数量的条件逻辑
- `hand_back_to_deck` — 手牌放回牌库（而非弃牌）

这触发了 `unsupported_or_needs_manual_review=true`，`candidate_ops_sequence` 为空，正确阻止了假阳性 simple sequence 的生成。

---

## 5. Draft preview 结果摘要

| 字段 | 值 |
|------|-----|
| `card_key` | ASR-150 |
| `draft_ready` | **false** |
| `unsupported_or_needs_manual_review` | **true** |
| `unsupported_reasons` | `["conditional_or_both_players_unsupported"]` |
| `candidate_ops_sequence` | `[]`（空） |
| draw count | N/A（无 `draw_cards` op 生成） |
| `risk_notes` | `["需要 runtime 支持: both_players, conditional_prize_count, hand_back_to_deck"]` |
| `meta.writes_semantic_ops_json` | false |
| `meta.calls_llm` | false |
| `meta.network_enabled` | false |
| `must_not_emit_final_json` | true |

---

## 6. Phase 7Y 准入检查

按照 Phase 7Y 模板第 4 节 checklist 逐项检查：

### 6.1 基础数据

| check | result | note |
|-------|--------|------|
| card_key 稳定 | **pass** | ASR-150，已在代码中固定 |
| local_file 存在 | **pass** | `ptcg/cards/ASR/asr150roxanne.py` |
| Trainer / Supporter | **pass** | 继承 `SupporterCard` |
| text 非空 | **pass** | refetch 成功获取中文文本 |

### 6.2 pipeline 状态

| check | result | note |
|-------|--------|------|
| prompt_ready | **pass** (true) | prompt preview 成功生成 |
| draft_ready | **FAIL** (false) | draft 标记为不可用 |
| unsupported_or_needs_manual_review | **FAIL** (true) | 触发 manual review |
| candidate_ops_sequence 不为空 | **FAIL** (空) | 序列被阻止生成 |

### 6.3 op 能力匹配

| check | result | note |
|-------|--------|------|
| 只使用 supported ops | **FAIL** | 效果需要 beyond-simple 能力 |
| 不需要新 runtime op | **FAIL** | 需要 both_players, conditional, hand_back_to_deck |

### 6.4 效果对齐

| check | result | note |
|-------|--------|------|
| draw count 明确 | **N/A** | 依赖于奖赏卡数量（conditional） |
| 可与 legacy resolve_ops 对齐 | **未检查** | draft 层面已拦截，无需对齐 |

### 6.5 排除条件

| check | result | note |
|-------|--------|------|
| 不涉及 both players | **FAIL** | 双方玩家均需放回手牌 |
| 不涉及 opponent | **FAIL** | 涉及对手手牌操作 |
| 不涉及 prize count | **FAIL** | 抽牌数依赖奖赏卡数量 |
| 不涉及 conditional | **FAIL** | "自己的剩余奖赏卡张数较多时" |
| 不涉及 shuffle / deck bottom | **隐含风险** | 手牌放回牌库（非弃牌区） |

---

## 7. Admission decision

### 结论：**Candidate must stay in manual review**

ASR-150 Roxanne 不满足 simple Supporter side-channel verification 的准入条件。

### 详细原因

1. **both_players**：Roxanne 的效果同时影响双方玩家（"双方玩家各将自己的手牌全部放回牌库"），当前 runtime 主要针对单玩家设计，缺少双方玩家统一处理语义
2. **hand_back_to_deck**：效果要求将手牌放回牌库（而非弃牌区），这与标准 `discard_cards` 操作不同——手牌回到牌库底部/任意位置需要额外的牌库操作能力
3. **conditional_prize_count**：抽牌数量不是固定值，而是依赖于"自己的剩余奖赏卡张数"的条件判断（"若自己的剩余奖赏卡张数较多，则抽 7 张；若对方的剩余奖赏卡张数较多，则抽 5 张"），需要条件分支 op
4. 这些能力在当前的 `_SUPPORTED_OPS` 中均不存在

### 本阶段不执行的操作

- 不进入 simple side-channel verification
- 不生成 side-channel PR
- 不生成 golden test
- 不生成 candidate_ops_sequence
- 不等价映射到 simple 4-step sequence（禁止降级语义）

### 解锁条件

ASR-150 需要以下 runtime op inventory 扩展后才能重新评估：

- `both_players` 操作支持
- `hand_to_deck` 或 `return_to_deck` 操作
- `conditional_branch` 或 `if_prize_count_more_than` 条件操作

在扩展完成前，ASR-150 应保持在 `manual_review / blocked` 状态。

---

## 8. 对后续流程的影响

### 8.1 Phase 7Y 模板是否有效

**是。** 本次准入检查过程完整验证了 Phase 7Y 模板的有效性：

- 模板定义的准入条件能正确区分 simple 和 complex Supporter
- `both_players`、`conditional`、`hand_back_to_deck` 等排除条件在 draft preview 中被正确触发
- `candidate_ops_sequence` 在检测到 unsupported 时正确生成空序列
- 模板的"必须停止并 manual review"（第 10 节）得到了实际操作验证

### 8.2 是否需要修改模板

暂不需要。当前模板覆盖了本次拦截的所有条件（both_players、conditional、hand_back_to_deck 均在第 1.3 节和第 10 节的排除列表中）。

### 8.3 是否发现新的 unsupported pattern

ASR-150 的 `hand_back_to_deck`（手牌放回牌库）是一个值得注意的模式：它既不是标准的 `discard_cards`（弃牌），也不是 `shuffle`（混合洗牌），而是"放回牌库顶部/任意位置"。

- 这在 golden summary 第 6 节已被提及（"hand_back_to_deck" 是 PAL-185 的阻挡原因之一）
- 确认 `hand_back_to_deck` 也是一个独立的 unsupported pattern

### 8.4 下一阶段方向

前 30 个候选中没有 simple discard-and-draw Supporter 进入 side-channel verification。建议两条路线：

**路线 A（优先）**：扩展 runtime op inventory

- 增加 shuffle / deck bottom / both players / conditional / prize count 能力
- 解锁 Iono、Judge、Roxanne 等复杂 Supporter
- 然后再回头对 simple Supporter 做更广范围的候选筛选

**路线 B**：继续在更广范围内搜索 simple Supporter

- 扩大 refetch plan 的扫描范围（超过前 30 个）
- 可能存在的简单 discard-and-draw Supporters 在其他系列中（如更多 Professor's Research 变体）
- 但当前前 30 个中显然没有，说明 simple draw Supporter 在整体卡池中的比例并不高

---

## 9. 安全边界

本报告明确声明以下操作**未被执行**：

| 操作 | 状态 |
|------|------|
| 修改 `ptcg/cards/` | 未执行 |
| 修改 `ptcg/core/` | 未执行 |
| 修改 tests | 未执行 |
| 修改 scripts | 未执行 |
| 修改 `ptcg/data_sources/` | 未执行 |
| 生成正式 `semantic_ops.json` | 未执行 |
| 生成 runtime-loadable ops 文件 | 未执行 |
| 覆盖 `card_chinese_data.json` | 未执行 |
| 覆盖 `card_data_cache.json` | 未执行 |
| preview 输出写入仓库 | 未执行（全部在 `%TEMP%\ptcg-refetch-preview\`） |

---

## 10. 下一阶段建议

### 如果继续筛选 simple Supporter

建议 Phase 8A：

1. 扩大候选搜索范围（超出前 30 个），查找更多 Professor's Research 变体或类似的 discard-all + draw-N 卡
2. 或者，确认当前整个卡池中没有更多 simple Supporter 可以进入 side-channel verification

### 如果优先扩展 runtime op inventory

建议 Phase 8B：

1. 设计 `both_players`、`shuffle`、`deck_bottom`、`conditional` 等新的 op 类型
2. 在 `ptcg/core/ops.py` 中添加对应的 `OpType` 枚举值
3. 更新 `_SUPPORTED_OPS` 集合
4. 然后重新对 Iono / Judge / Roxanne 进行准入评估

### 本阶段产出

- `docs/simple_supporter_next_candidate_admission_report.md`（本报告）
- 仓库外 preview 文件（`phase7z_asr150_*_preview.json`）
- 无代码修改
