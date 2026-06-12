# Normalized Card Text Layer Design

## 目标

`normalized card text layer` 的目标是把现有缓存、爬取数据、本地卡牌文件映射和未来补抓文本统一成一个稳定、可追踪、可用于 prompt 的数据层。

它不是为了替代现有 JSON，而是为后续流程提供统一输入：

现有 JSON
-> normalized card text layer
-> semantic extraction prompt
-> semantic ops JSON
-> side-channel test generator
-> single-card PR

设计目标：

- 统一 identity、类型、文本、映射和 provenance
- 区分字段“是否存在”和“是否可信”
- 支持部分缺字段卡牌先进入待补抓队列，而不是直接失败
- 让后续 prompt 层只消费一个稳定 schema，而不是同时理解多个上游格式
- 保证 normalized 层是 `derived artifact`，可重复生成，可追踪版本和来源

## 非目标

本阶段不做以下事情：

- 不覆盖 `card_chinese_data.json`
- 不覆盖 `card_data_cache.json`
- 不直接爬取 `tcg.mik.moe`
- 不生成 prompt
- 不生成测试
- 不修改卡牌实现
- 不接入 semantic op runtime
- 不新增 loader、爬虫或网络客户端实现
- 不实际创建 normalized JSON 输出

## 输入来源

### 1. `card_chinese_data.json`

提供字段：

- `name`
- `set_name`
- `number`
- `chinese_name`
- `set_code_cn`
- `card_index_cn`
- `image_url`
- `attacks_en`
- `attacks_cn`
- `abilities_en`
- `abilities_cn`
- `hp`
- `file`
- `match_score`
- `match_method`

可信字段：

- `set_name`
- `number`
- `chinese_name`
- `file`
- `set_code_cn`
- `card_index_cn`
- `match_score`
- `match_method`

低可信或不完整字段：

- `attacks_cn`
- `abilities_cn`
- 不包含 Trainer/Supporter 完整规则文本
- 不包含攻击/特性的完整中文效果句

是否需要 provenance：

- 需要
- 尤其是 `file`、`chinese_name`、`set_code_cn`、`card_index_cn`、`match_score`、`match_method`

### 2. `card_data_cache.json`

提供字段：

- `name`
- `set_name`
- `number`
- `card_type`
- `img`
- `hp`
- `attacks`
- `abilities`
- `attacks_en`
- `attacks_cn`
- `abilities_en`
- `abilities_cn`

可信字段：

- `set_name`
- `number`
- `name`
- `attacks[]` 和 `abilities[]` 的“存在性”可作为辅助信号

不可信字段：

- `card_type`

当前已知问题：

- 207 条记录的 `card_type` 全部为 `Pokemon`
- 缺少 `effect_text`
- 缺少 Trainer/Supporter 规则文本
- 缺少稳定 provenance

是否需要 provenance：

- 需要
- 必须将 `card_type` 标记为低可信来源

### 3. `tcg.mik.moe card-detail`，未来补抓

预期可提供字段：

- `description`
- `cardType`
- `pokemonAttr.attack[].name`
- `pokemonAttr.attack[].text`
- `pokemonAttr.attack[].cost`
- `pokemonAttr.attack[].damage`
- `pokemonAttr.ability[].name`
- `pokemonAttr.ability[].text`
- `pokemonAttr.ability[].type`

可信字段：

- `description`
- `cardType`
- `pokemonAttr.attack[].text`
- `pokemonAttr.ability[].text`

需要警惕：

- 上游字段名或结构可能变化
- 同一信息在历史脚本里存在 `text` vs `effect` 错位

是否需要 provenance：

- 强制需要
- 需要记录 `fetched_at`、`source_url`、`source_api`、`raw_id`

### 4. 本地 `ptcg/cards/**/*.py`

提供字段：

- 本地文件路径
- 本地类名
- Python 类继承关系
- `self.text`
- `self.name`
- `self.set_name`
- `self.number`
- `attacks[].text`
- `abilities[].text`

可信字段：

- `local_file`
- `local_class_name`
- 继承关系推断的 `card_supertype`
- `SupporterCard` / `ItemCard` / `StadiumCard` / `ToolCard` / `PokemonCard` / `EnergyCard`
- 已实现卡的本地中文文本

需要注意：

- 本地代码可能是历史实现，不一定和上游中文页面逐字一致
- 未编号文件无法仅靠文件名反推出 `set+number`

是否需要 provenance：

- 需要
- 本地源码是类型判断的最高优先级来源

### 5. 可能的脚本输出，例如 `generate_card_cache.py`

可提供字段：

- `card_type`
- `trainer_type`
- `effect_text`
- `attacks[].text`
- `abilities[].text`
- `super_type`

可信度：

- 高于当前根目录 `card_data_cache.json`
- 低于直接读取本地源码的实时扫描结果

是否需要 provenance：

- 需要
- 应记录生成脚本版本和运行时间

## 输出位置建议

建议输出位置之一：

- `data/normalized_card_text.json`

如果当前仓库暂不建立 `data/` 目录，也可以采用：

- `card_normalized_text_cache.json`

推荐优先方案：

- `data/normalized_card_text.json`

原因：

- 明确表明这是派生数据层
- 避免与现有根目录缓存混淆
- 更适合后续增加 preview、manifest 和 provenance 辅助文件

本阶段只做设计，不实际创建任何 JSON 文件。

## 核心 schema

normalized record 以单卡为单位，顶层建议结构如下：

```json
{
  "card_key": "TWM-145",
  "identity": {},
  "classification": {},
  "text": {},
  "attacks": [],
  "abilities": [],
  "quality_flags": {},
  "provenance": {},
  "meta": {}
}
```

### identity

建议字段：

- `card_key`
- `set_code`
- `set_name`
- `number`
- `normalized_number`
- `name_en`
- `name_zh`
- `local_file`
- `local_class_name`
- `source_ids`

字段说明：

- `card_key`
  - 推荐标准格式：`SET-NUMBER`
  - 例如：`TWM-145`
- `set_code`
  - 推荐与 `set_name` 保持一致，统一存英文 set code
- `set_name`
  - 保留上游原字段，便于兼容现有输入
- `number`
  - 保留原始编号字符串
- `normalized_number`
  - 用于比较和映射，去前导零
- `name_en`
  - 若缺失可为 `null`
- `name_zh`
  - 当前多数记录可来自 `card_chinese_data.json`
- `local_file`
  - 绝对或仓库相对路径，推荐仓库相对路径
- `local_class_name`
  - 例如 `TWM145Carmine`
- `source_ids`
  - 记录上游标识，例如：
  - `card_data_cache_key`
  - `card_chinese_key`
  - `mik_set_code`
  - `mik_card_index`

### classification

建议字段：

- `card_supertype`
- `trainer_subtype`
- `pokemon_stage`
- `energy_type`
- `classification_confidence`
- `classification_source`
- `classification_warnings`

字段说明：

- `card_supertype`
  - `Pokemon` / `Trainer` / `Energy` / `Unknown`
- `trainer_subtype`
  - `Supporter` / `Item` / `Stadium` / `Tool` / `Unknown`
- `pokemon_stage`
  - `Basic` / `Stage 1` / `Stage 2` / `Unknown` / `null`
- `energy_type`
  - 仅对能量卡有意义
- `classification_confidence`
  - `high` / `medium` / `low`
- `classification_source`
  - `local_class`
  - `tcg_mik_detail.cardType`
  - `generate_card_cache`
  - `card_data_cache.card_type`
  - `heuristic`
- `classification_warnings`
  - 数组，例如：
  - `["card_data_cache.card_type_untrusted"]`

### text

建议字段：

- `rules_text_zh`
- `rules_text_en`
- `trainer_text_zh`
- `trainer_text_en`
- `full_text_zh`
- `full_text_en`
- `text_available`
- `text_quality`

字段说明：

- `rules_text_zh`
  - 通用规则文本字段
- `trainer_text_zh`
  - Trainer/Supporter/Item/Stadium/Tool 的专用文本字段
- `full_text_zh`
  - 统一拼装后的 prompt 主文本
  - 对 Trainer 通常等于 `trainer_text_zh`
  - 对 Pokemon 可由 attacks、abilities、rule box 组成
- `text_available`
  - 是否已有足够文本进入下游
- `text_quality`
  - `complete` / `partial` / `missing`

设计约束：

- 不编造文本
- 缺失时明确存 `null`
- 对 Trainer 文本缺失必须显式打标，而不是默认为空字符串

### attacks

每个 `attack` 至少包含：

- `name_en`
- `name_zh`
- `cost`
- `damage`
- `effect_text_en`
- `effect_text_zh`
- `source`

建议单条结构：

```json
{
  "name_en": null,
  "name_zh": "攻击名",
  "cost": ["FIRE", "COLORLESS"],
  "damage": {
    "amount": 120,
    "suffix": ""
  },
  "effect_text_en": null,
  "effect_text_zh": null,
  "source": {
    "primary": "card_data_cache.attacks",
    "secondary": ["tcg_mik_detail.pokemonAttr.attack"]
  }
}
```

### abilities

每个 `ability` 至少包含：

- `name_en`
- `name_zh`
- `ability_type`
- `effect_text_en`
- `effect_text_zh`
- `source`

建议单条结构：

```json
{
  "name_en": null,
  "name_zh": "特性名",
  "ability_type": "ABILITY",
  "effect_text_en": null,
  "effect_text_zh": null,
  "source": {
    "primary": "card_data_cache.abilities",
    "secondary": ["tcg_mik_detail.pokemonAttr.ability"]
  }
}
```

### provenance

每个重要字段都需要可追踪来源。

可选方案：

#### 方案 A：字段级 provenance

```json
{
  "provenance": {
    "name_zh": {
      "source": "card_chinese_data.json",
      "field": "chinese_name"
    }
  }
}
```

优点：

- 最精确
- 对审计和排错最好
- 非常适合追踪多源字段合并

缺点：

- 输出体积大
- 编码实现较啰嗦

#### 方案 B：记录级 provenance + field_source_map

```json
{
  "provenance": {
    "sources": [
      {
        "id": "card_chinese_data",
        "type": "json",
        "path": "card_chinese_data.json"
      }
    ],
    "field_source_map": {
      "identity.name_zh": "card_chinese_data",
      "identity.local_file": "card_chinese_data",
      "classification.card_supertype": "local_class"
    }
  }
}
```

优点：

- 更紧凑
- 更容易实现
- 更适合先落地第一版

缺点：

- 单字段细节稍弱
- 对数组字段的来源表达不如方案 A 直观

推荐：

- **推荐方案 B**

原因：

- 第一版 normalized 层优先追求可落地和可维护
- `field_source_map` 已足够满足后续 prompt、调试和补抓审计需求
- 对 `attacks[]`、`abilities[]` 可在元素级再附加 `source`

### quality flags

必须包含：

- `missing_rules_text`
- `untrusted_card_type`
- `missing_local_file`
- `ambiguous_mapping`
- `needs_text_refetch`
- `needs_type_refetch`
- `unsupported_for_prompt`
- `prompt_ready`

建议补充：

- `missing_effect_text`
- `missing_name_zh`
- `missing_name_en`
- `derived_from_partial_sources`
- `legacy_cache_shape_mismatch`

## 示例记录

以下示例只体现结构，不编造不存在的完整卡牌效果文本。

### 示例 1: TWM145 Carmine

```json
{
  "card_key": "TWM-145",
  "identity": {
    "card_key": "TWM-145",
    "set_code": "TWM",
    "set_name": "TWM",
    "number": "145",
    "normalized_number": "145",
    "name_en": "Carmine",
    "name_zh": "丹瑜",
    "local_file": "ptcg/cards/TWM/twm145carmine.py",
    "local_class_name": "TWM145Carmine",
    "source_ids": {
      "card_chinese_key": "cards/TWM/twm145carmine",
      "card_data_cache_key": "TWM-145",
      "mik_set_code": "CSVNC",
      "mik_card_index": "037"
    }
  },
  "classification": {
    "card_supertype": "Trainer",
    "trainer_subtype": "Supporter",
    "pokemon_stage": null,
    "energy_type": null,
    "classification_confidence": "high",
    "classification_source": "local_class",
    "classification_warnings": [
      "card_data_cache.card_type_untrusted"
    ]
  },
  "text": {
    "rules_text_zh": null,
    "rules_text_en": null,
    "trainer_text_zh": null,
    "trainer_text_en": null,
    "full_text_zh": null,
    "full_text_en": null,
    "text_available": false,
    "text_quality": "missing"
  },
  "attacks": [],
  "abilities": [],
  "quality_flags": {
    "missing_rules_text": true,
    "untrusted_card_type": true,
    "missing_local_file": false,
    "ambiguous_mapping": false,
    "needs_text_refetch": true,
    "needs_type_refetch": false,
    "unsupported_for_prompt": true,
    "prompt_ready": false
  },
  "provenance": {
    "sources": [
      {
        "id": "card_chinese_data",
        "type": "json",
        "path": "card_chinese_data.json"
      },
      {
        "id": "card_data_cache",
        "type": "json",
        "path": "card_data_cache.json"
      },
      {
        "id": "local_class",
        "type": "python",
        "path": "ptcg/cards/TWM/twm145carmine.py"
      }
    ],
    "field_source_map": {
      "identity.name_zh": "card_chinese_data",
      "identity.local_file": "card_chinese_data",
      "classification.card_supertype": "local_class",
      "classification.trainer_subtype": "local_class",
      "text.trainer_text_zh": "missing"
    }
  },
  "meta": {
    "generated_at": "TBD",
    "generator_version": "v0-design"
  }
}
```

### 示例 2: SSH178 Professor's Research

```json
{
  "card_key": "SSH-178",
  "identity": {
    "card_key": "SSH-178",
    "set_code": "SSH",
    "set_name": "SSH",
    "number": "178",
    "normalized_number": "178",
    "name_en": "Professor's Research",
    "name_zh": "博士的研究",
    "local_file": "ptcg/cards/SSH/ssh178professorsresearch.py",
    "local_class_name": "SSH178ProfessorsResearch",
    "source_ids": {
      "card_chinese_key": "cards/SSH/ssh178professorsresearch",
      "card_data_cache_key": "SSH-178",
      "mik_set_code": "CSVH4eC",
      "mik_card_index": "047"
    }
  },
  "classification": {
    "card_supertype": "Trainer",
    "trainer_subtype": "Supporter",
    "pokemon_stage": null,
    "energy_type": null,
    "classification_confidence": "high",
    "classification_source": "local_class",
    "classification_warnings": [
      "card_data_cache.card_type_untrusted"
    ]
  },
  "text": {
    "rules_text_zh": null,
    "rules_text_en": null,
    "trainer_text_zh": null,
    "trainer_text_en": null,
    "full_text_zh": null,
    "full_text_en": null,
    "text_available": false,
    "text_quality": "missing"
  },
  "attacks": [],
  "abilities": [],
  "quality_flags": {
    "missing_rules_text": true,
    "untrusted_card_type": true,
    "missing_local_file": false,
    "ambiguous_mapping": false,
    "needs_text_refetch": true,
    "needs_type_refetch": false,
    "unsupported_for_prompt": true,
    "prompt_ready": false
  }
}
```

### 示例 3: PAL185 Iono

```json
{
  "card_key": "PAL-185",
  "identity": {
    "card_key": "PAL-185",
    "set_code": "PAL",
    "set_name": "PAL",
    "number": "185",
    "normalized_number": "185",
    "name_en": "Iono",
    "name_zh": "奇树",
    "local_file": "ptcg/cards/PAL/pal185iono.py",
    "local_class_name": "PAL185Iono",
    "source_ids": {
      "card_chinese_key": "cards/PAL/pal185iono",
      "card_data_cache_key": "PAL-185"
    }
  },
  "classification": {
    "card_supertype": "Trainer",
    "trainer_subtype": "Supporter",
    "pokemon_stage": null,
    "energy_type": null,
    "classification_confidence": "high",
    "classification_source": "local_class",
    "classification_warnings": [
      "card_data_cache.card_type_untrusted"
    ]
  },
  "text": {
    "rules_text_zh": null,
    "rules_text_en": null,
    "trainer_text_zh": null,
    "trainer_text_en": null,
    "full_text_zh": null,
    "full_text_en": null,
    "text_available": false,
    "text_quality": "missing"
  },
  "attacks": [],
  "abilities": [],
  "quality_flags": {
    "missing_rules_text": true,
    "untrusted_card_type": true,
    "missing_local_file": false,
    "ambiguous_mapping": false,
    "needs_text_refetch": true,
    "needs_type_refetch": false,
    "unsupported_for_prompt": true,
    "prompt_ready": false
  }
}
```

## 匹配策略

normalized 层将上游记录映射到本地卡牌文件时，按以下优先级执行：

1. 优先使用 `card_chinese_data.json` 的 `file` 字段
2. 其次使用 `set_name + normalized(number)`
3. 再其次使用本地文件名解析
4. 对无编号文件使用 `file` 字段或 name-based fallback
5. 如果多个候选同时匹配，标记 `ambiguous_mapping=true`，不自动选择

### 规则细化

#### 一级：`card_chinese_data.json.file`

- 这是当前最稳定的桥接字段
- 若 `file` 能命中本地真实路径，则直接采用

#### 二级：`set_name + normalized(number)`

- 用于匹配：
  - `card_data_cache.json`
  - `generate_card_cache.py` 输出
  - 可编号的本地文件

#### 三级：本地文件名解析

- 适用于 `twm145carmine.py`、`ssh178professorsresearch.py`、`pal185iono.py`
- 从文件名解析 `set+number`

#### 四级：name-based fallback

- 仅在无编号文件时使用
- 例如：
  - `ptcg/cards/PAF/professors_research.py`
  - `ptcg/cards/ASC/lillies_determination.py`

要求：

- name-based fallback 必须结合 set 目录或 `card_chinese_data.json.file`
- 不允许只凭名称自动强绑多候选卡

#### 歧义处理

- 若出现多个候选：
  - 设置 `ambiguous_mapping=true`
  - 设置 `unsupported_for_prompt=true`
  - 不自动挑选单一文件

## 类型判断策略

由于 `card_data_cache.json.card_type` 不可信，类型判断必须重建优先级。

推荐优先级：

1. 本地 Python 类继承关系
2. `tcg.mik.moe card-detail.cardType`
3. `generate_card_cache.py` 的提取结果
4. `card_data_cache.json.card_type`，仅作为低可信 fallback
5. 文件路径、类名、名称启发式

具体规则：

- 若本地类继承 `SupporterCard`，则：
  - `card_supertype = Trainer`
  - `trainer_subtype = Supporter`
- 若继承 `ItemCard` / `StadiumCard` / `ToolCard`，同理推断
- 若继承 `PokemonCard`，则：
  - `card_supertype = Pokemon`
- 若继承 `EnergyCard`，则：
  - `card_supertype = Energy`

明确约束：

- `card_data_cache.json.card_type` 默认不可信
- 若最终类型只能来自不可信源，必须设置：
  - `untrusted_card_type = true`
  - `needs_type_refetch = true`
  - `classification_confidence = low`

## 文本补抓策略

未来补抓目标字段：

- `rules_text_zh`
- `trainer_text_zh`
- `attack.effect_text_zh`
- `ability.effect_text_zh`
- `card_supertype`
- `trainer_subtype`

策略要求：

1. 不优先全量重爬
2. 优先定向补抓 prompt 需要的卡
3. 优先 Trainer / Supporter
4. 优先 P0/P1 候选卡
5. 补抓结果写入 normalized 层，而不是覆盖原 JSON
6. 每个补抓字段都记录 provenance
7. 缓存 `fetched_at`、`source_url`、`source_api`、`raw_id`

建议补抓顺序：

1. `missing_rules_text=true` 且 `card_supertype=Trainer`
2. P0/P1 候选卡
3. `missing_effect_text=true` 的 Pokemon
4. `untrusted_card_type=true` 且本地类缺失的卡

优先字段：

- `tcg_mik_detail.description`
- `tcg_mik_detail.cardType`
- `tcg_mik_detail.pokemonAttr.attack[].text`
- `tcg_mik_detail.pokemonAttr.ability[].text`

## prompt readiness 判断

`prompt_ready=true` 必须满足以下条件：

- `local_file` 存在
- `card_supertype` 可信
- 没有 `ambiguous_mapping`
- 没有阻断性 quality flags

对不同类别追加规则：

### Trainer / Supporter / Item / Stadium / Tool

必须满足：

- `rules_text_zh` 或 `trainer_text_zh` 至少一个存在

否则：

- `missing_rules_text = true`
- `unsupported_for_prompt = true`
- `prompt_ready = false`

### Pokemon

必须满足之一：

- 至少一条 attack 或 ability 具有完整 `effect_text_zh`
- 或明确没有效果文本，但结构完整且可证明为纯伤害/纯数值卡

否则：

- `missing_effect_text = true`
- `prompt_ready = false`

### Energy

必须满足：

- 基础能量：可仅凭类型进入 prompt
- 特殊能量：必须有 `rules_text_zh`

否则：

- `unsupported_for_prompt = true`

### unsupported reason

建议输出数组 `unsupported_reasons`，候选值包括：

- `missing_rules_text`
- `ambiguous_local_file`
- `untrusted_card_type`
- `missing_effect_text`
- `unsupported_card_category`
- `missing_local_file`
- `missing_required_text`

## 与 semantic ops 的关系

normalized text layer 不直接生成 ops。

它只提供 prompt 输入。

后续流程应为：

normalized record
-> semantic extraction prompt
-> semantic ops draft JSON
-> validation
-> side-channel test generation
-> optional `resolve_ops` patch

设计原则：

- normalized 层提供事实材料
- semantic prompt 负责语义抽取
- validator 负责约束 schema 和安全边界
- test generator 负责旁路验证
- 代码补丁是最终可选结果，而不是 normalized 层职责

## 与现有数据文件的关系

必须明确：

- 不直接覆盖 `card_chinese_data.json`
- 不直接覆盖 `card_data_cache.json`
- 这两个文件都是 upstream input
- normalized layer 是 derived artifact
- normalized layer 应可重复生成
- normalized layer 应记录生成时间和生成版本

建议元字段：

- `generated_at`
- `generator_version`
- `input_versions`
- `schema_version`

## 推荐文件结构

未来建议结构：

```text
ptcg/data_sources/
  normalized_card_text.py
  tcg_mik_client.py
  cache_loader.py

data/
  normalized_card_text.json

docs/
  normalized_card_text_layer_design.md
```

说明：

- `normalized_card_text.py`
  - 负责合成 normalized records
- `tcg_mik_client.py`
  - 未来如需定向补抓，统一放这里
- `cache_loader.py`
  - 负责读取现有 JSON 与本地索引
- `normalized_card_text.json`
  - 存派生结果

本阶段不要创建这些文件。

## 下一阶段建议

### Phase 7D: implement normalized card text loader without network

目标：

- 读取 `card_chinese_data.json`
- 读取 `card_data_cache.json`
- 读取本地 `ptcg/cards`
- 合成 normalized records
- 不联网
- 不补抓
- 输出 `data/normalized_card_text.preview.json` 或只在测试里生成
- 加最小单测验证 `TWM145` / `SSH178` / `PAL185`

建议范围：

- 只实现 identity + classification + quality flags + 基础 text 占位
- 不做 refetch
- 不覆盖原始缓存

### Phase 7E: targeted text refetch design or implementation

目标：

- 只对 `missing_rules_text` 的卡定向补抓
- 先 dry-run
- 不覆盖原 JSON

建议优先顺序：

- `Trainer` / `Supporter`
- P0/P1 候选卡
- 再处理 Pokemon effect text 缺口

## 风险

- 上游 API/page 变动
- 中文文本缺失
- 类型字段不可信
- 本地文件映射歧义
- prompt 使用半残文本误判
- normalized 层和原始缓存不同步
- provenance 缺失导致无法追责
- 重爬污染原缓存
- `text` vs `effect` 字段错位导致误采集
- 无编号文件引入错误 name-based 绑定
