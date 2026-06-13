# Normalized Patch Application Design

## 目标

基于 Phase 7L 完成的 `refetch_card_text_preview.py` 输出（即 `normalized_patch_preview` + `provenance_preview` + `response_diagnostics`），设计如何安全地将 refetch 结果应用到 derived normalized layer。

本阶段只做设计 / 审计，不实现 patch application，不生成正式 normalized JSON。

## 非目标

本阶段明确不做：

- 不覆盖 `card_chinese_data.json`
- 不覆盖 `card_data_cache.json`
- 不生成正式 `data/normalized_card_text.json`
- 不生成 prompt
- 不生成 semantic ops JSON
- 不修改 `ptcg/cards`
- 不修改 `ptcg/core`
- 不接入 reducer / env.step
- 不修改 semantic runtime

## 1. Current successful preview observation

### 1.1 TWM-145 preview 摘要

| 维度 | 值 |
|------|-----|
| `card_key` | TWM-145 |
| `name_zh` | 丹瑜 |
| `source` | tcg.mik.moe card-detail |
| `lookup_strategy` | detail_by_source_ids |
| `raw_fields_found` | `["cardType", "description"]` |
| `errors` | `[]` |
| `warnings` | `[]` |
| `network_enabled` | true |
| `dry_run` | false |
| `writes_original_cache` | false |
| `writes_normalized_cache` | false |

### 1.2 parsed_fields

- `cardType`: `"Supporter"`
- `description`: 存在（包含支持者规则文本 + 效果文本，共约 60 字）

### 1.3 normalized_patch_preview

| 路径 | 是否填充 |
|------|----------|
| `text.rules_text_zh` | 是 |
| `text.trainer_text_zh` | 是 |
| `text.full_text_zh` | 是 |
| `classification.card_supertype` | `"Trainer"` |
| `classification.trainer_subtype` | `"Supporter"` |

### 1.4 response_diagnostics

| 字段 | 值 |
|------|-----|
| `response_shape` | `"flat"` |
| `description_path` | `$.description` |
| `card_type_path` | `$.cardType` |
| `has_description` | true |
| `has_card_type` | true |

### 1.5 关键结论

- TWM-145 的 refetch 完全成功，无 error 无 warning
- `response_shape` 为 `flat`（非 `fetch_error`、非嵌套），可直接提取顶端字段
- `description` 与 `cardType` 均命中，diagnostics 路径正确
- `normalized_patch_preview` 的 `text` 和 `classification` 均已填充

## 2. Patch application target

Patch application 的目标是 **derived normalized records**（即 `normalized_card_text_layer_design.md` 定义的标准化记录）。

明确排除：

| 排除目标 | 原因 |
|----------|------|
| `card_chinese_data.json` | 原始缓存，不可覆盖 |
| `card_data_cache.json` | 原始缓存，不可覆盖 |
| `ptcg/cards/**/*.py` | 本地源码，不可自动修改 |
| semantic ops JSON | 属于下游 prompt 层，不在此阶段生成 |
| prompt | 属于下游，不在此阶段生成 |

## 3. Proposed patch application API

### 3.1 函数签名（未来实现）

```python
def apply_refetch_result_to_normalized_record(
    record: dict,
    refetch_result: dict,
    *,
    overwrite_non_empty: bool = False,
    disallow_output_paths: set[str] | None = None,
) -> dict:
```

### 3.2 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| `record` | `dict` | 现有 normalized record |
| `refetch_result` | `dict` | `results[0]` from refetch preview JSON |
| `overwrite_non_empty` | `bool` | 是否允许覆盖已有非空字段，默认 `False` |
| `disallow_output_paths` | `set[str]` | 禁止写入的路径集合 |

从 `refetch_result` 中提取子结构：

- `refetch_result["normalized_patch_preview"]`
- `refetch_result["provenance_preview"]`
- `refetch_result["response_diagnostics"]`
- `refetch_result["errors"]`
- `refetch_result["warnings"]`

### 3.3 输出

```python
{
    "updated_record": dict,        # 应用 patch 后的 normalized record
    "applied_fields": list[str],   # 实际写入的字段路径
    "skipped_fields": list[str],   # 被跳过未写入的字段及原因
    "warnings": list[str],         # 合并后的 warnings
    "errors": list[str],           # 合并后的 errors
}
```

### 3.4 调用关系

```
refetch preview JSON
  -> extract refetch_result
    -> apply_refetch_result_to_normalized_record(record, refetch_result)
      -> updated_record + application_report
```

## 4. Field merge policy

### 4.1 text 字段

允许从 `normalized_patch_preview.text` 写入的字段：

- `text.rules_text_zh`
- `text.trainer_text_zh`
- `text.full_text_zh`

写入条件（全部满足）：

1. patch field 值非空（非 `None`、非 `""`）
2. `response_diagnostics.has_description == true`
3. `refetch_result.errors` 为空列表 `[]`
4. source trusted（即 `response_shape != "fetch_error"`）
5. `existing field` 为空，或 `overwrite_non_empty == true`

默认行为：不覆盖已有非空字段。跳过时记录 `skipped_fields` 及原因。

### 4.2 classification 字段

允许从 `normalized_patch_preview.classification` 写入的字段：

- `classification.card_supertype`
- `classification.trainer_subtype`

写入条件（全部满足）：

1. `response_diagnostics.has_card_type == true`
2. `cardType` 可映射为受支持类型
3. source priority 高于 `card_data_cache.card_type`（后者已知不可信）
4. 不与 local Python class inheritance 冲突

冲突处理规则：

| 场景 | 行为 |
|------|------|
| local class = `Trainer/Supporter`, refetch = `Supporter` | 确认，可写入 |
| local class = `Trainer/Supporter`, refetch = `Item/Stadium/Tool` | 不覆盖，添加 `quality_flag`，添加 `warning` |
| local class = `Pokemon`, refetch = `Pokemon` | 确认（但 source priority 在 local 之下） |
| local class = `Trainer/Supporter`, refetch 缺失 `cardType` | 不写入，保留 local |

### 4.3 字段合并优先级

```
1. local Python class inheritance (最高)
2. tcg.mik.moe card-detail.cardType (refetch, trusted)
3. card_chinese_data.json (中等)
4. card_data_cache.json.card_type (最低，已知不可信)
```

## 5. Quality flag updates

TWM-145 成功应用后的 quality flag 变化：

| flag | 应用前（假设） | 应用后 | 说明 |
|------|---------------|--------|------|
| `missing_rules_text` | `true` | `false` | rules_text_zh 已从 description 填充 |
| `needs_text_refetch` | `true` | `false` | 已成功 refetch |
| `missing_effect_text` | — | `false` | Supporter 卡牌的 description 覆盖了效果文本 |
| `untrusted_card_type` | `true` | `false` 或保留 source-specific 注释 | 若 classification 被 trusted source 修正 |

### 5.1 prompt_ready 重新计算

`prompt_ready` **不能简单设为 `true`**，必须按 `normalized_card_text_layer_design.md` 的规则重新计算：

```
prompt_ready = (
    text.full_text_zh 非空
    AND classification.card_supertype 非空
    AND 对于 Pokemon 卡牌：攻击和特性文本完整
)
```

TWM-145 是 Supporter 卡牌，有 `full_text_zh` 和 `classification`，因此 `prompt_ready` 应为 `true`。

## 6. Provenance policy

### 6.1 record-level provenance

在 normalized record 的顶层 provenance 中追加 refetch 来源：

```json
{
  "provenance": {
    "sources": [
      {
        "source": "tcg.mik.moe card-detail",
        "fetched_at": "2026-06-13T...",
        "request": {
          "setCode": "CSVNC",
          "cardIndex": "037"
        },
        "response_diagnostics_summary": {
          "response_shape": "flat",
          "has_description": true,
          "has_card_type": true
        }
      }
    ]
  }
}
```

禁止保存完整 raw response。

### 6.2 field_source_map

记录每个字段的来源：

| 字段 | 来源 |
|------|------|
| `text.rules_text_zh` | `tcg.mik.moe card-detail.description` |
| `text.trainer_text_zh` | `tcg.mik.moe card-detail.description` |
| `text.full_text_zh` | `tcg.mik.moe card-detail.description` |
| `classification.card_supertype` | `tcg.mik.moe card-detail.cardType` |
| `classification.trainer_subtype` | `tcg.mik.moe card-detail.cardType` |

## 7. Safety policy

### 7.1 禁止项（硬约束）

| 禁止操作 | 原因 |
|----------|------|
| 覆盖 `card_chinese_data.json` | 原始缓存，不可修改 |
| 覆盖 `card_data_cache.json` | 原始缓存，不可修改 |
| 自动覆盖已有人工修正字段 | 保持人工修正不被静默覆盖 |
| 缺 `response_diagnostics` 时应用 patch | 无 diagnostics 无法判断数据质量 |
| `errors` 非空时应用 patch | 有错误说明来源不可靠 |
| `response_shape == "fetch_error"` 时应用 patch | fetch 层已失败 |
| `has_description == false` 时写 text 字段 | 无数据源 |
| `has_card_type == false` 时写 classification 字段 | 无数据源 |
| 直接应用到 `ptcg/cards` | 本地源码不可自动修改 |
| 直接生成 semantic ops JSON | 属于下游阶段 |

### 7.2 软约束

- 默认不覆盖已有非空字段（需 `overwrite_non_empty=True` 显式允许）
- 每次 patch 应用必须产出 `applied_fields` / `skipped_fields` 报告
- 每个 skipped field 必须附带原因

## 8. CLI future design

### 8.1 命令

```
scripts/apply_refetch_preview.py
```

### 8.2 参数设计

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--input-preview` | `path` | 必填 | refetch preview JSON 路径 |
| `--input-normalized` | `path` | 必填 | 现有 normalized records 路径 |
| `--output-report` | `path` | 可选 | patch application report 输出路径 |
| `--output-normalized-preview` | `path` | 可选 | 应用后的 normalized record preview 路径 |
| `--card-key` | `str` | 可选 | 只处理指定 card_key |
| `--overwrite` | `flag` | false | 允许覆盖已有非空字段 |
| `--dry-run` | `flag` | true（默认） | 不写文件 |

### 8.3 默认行为

- 默认 `--dry-run`：只输出 report，不写任何文件
- 只有显式 `--output-normalized-preview` 才写入 preview artifact
- 禁止输出到以下路径（硬编码拒绝）：
  - `card_chinese_data.json`
  - `card_data_cache.json`
  - `data/normalized_card_text.json`（除非未来明确进入正式生成阶段）

### 8.4 使用示例

```
# 默认 dry-run，仅输出 report
uv run python scripts/apply_refetch_preview.py \
  --input-preview twm145_preview.json \
  --input-normalized data/normalized_card_text.json

# 输出 preview artifact（仍不覆盖正式 JSON）
uv run python scripts/apply_refetch_preview.py \
  --input-preview twm145_preview.json \
  --input-normalized data/normalized_card_text.json \
  --output-report report.json \
  --output-normalized-preview twm145_applied_preview.json
```

## 9. Tests future design

### 9.1 需实现的测试用例

| # | 测试名称 | 描述 |
|---|---------|------|
| 1 | `test_successful_twm145_patch_application` | TWM-145 正常应用，text 和 classification 均写入 |
| 2 | `test_errors_non_empty_does_not_apply` | errors 非空时整个 patch 被拒绝 |
| 3 | `test_missing_description_skips_text` | has_description=false 时跳过 text 字段写入 |
| 4 | `test_missing_cardtype_skips_classification` | has_card_type=false 时跳过 classification 写入 |
| 5 | `test_local_class_conflict_no_overwrite` | 本地继承判断与 refetch 冲突时不覆盖 |
| 6 | `test_existing_non_empty_field_no_overwrite` | 已有非空字段默认不被覆盖 |
| 7 | `test_overwrite_flag_allows_overwrite` | overwrite_non_empty=True 时允许覆盖非空字段 |
| 8 | `test_provenance_field_source_map_correct` | field_source_map 记录正确的来源映射 |
| 9 | `test_quality_flags_recalculated` | quality flags（missing_*, needs_refetch）正确更新 |
| 10 | `test_dangerous_output_path_rejected` | 禁止写入 card_chinese_data.json 等受保护路径 |
| 11 | `test_original_json_unchanged` | 验证原始 JSON 未被修改 |
| 12 | `test_fetch_error_shape_rejected` | response_shape=fetch_error 时拒绝应用 |

### 9.2 测试数据

- 使用 fixture / mocked preview JSON，不联网
- TWM-145 的成功 preview 可用作 golden fixture
- 可构造 error / missing / conflict 场景的 fixture

## 10. Recommended next phase

### Phase 7N: implement patch application as in-memory dry-run only

范围：

- 实现 `apply_refetch_result_to_normalized_record()` 函数
- 放在 `ptcg/data_sources/` 下，不联网
- 输入 refetch result + normalized record
- 输出 `updated_record` preview + `application_report`
- 不写正式 JSON
- 不覆盖原始 JSON
- tests only with fixture / mocked preview data
- 不联网

### 后续阶段（概览，不展开）

- Phase 7O: 批量 refetch 计划内卡牌并输出 previews
- Phase 7P: 批量 apply patch 到 normalized records
- Phase 7Q: 正式生成 `data/normalized_card_text.json`（需用户确认）
