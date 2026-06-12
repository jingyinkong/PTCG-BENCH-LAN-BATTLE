# Card Data Cache Audit

## 目标

本报告用于审计现有 `card_chinese_data.json` 和 `card_data_cache.json` 是否可以作为后续中文卡牌信息、prompt 语义解析、测试生成的数据源。

本阶段只审计现有数据资产，不修改任何 JSON，不修改任何卡牌代码，不修改语义层代码。

## 文件位置

- `F:\PTCG-BENCH-LAN-BATTLE\card_chinese_data.json`
- `F:\PTCG-BENCH-LAN-BATTLE\card_data_cache.json`

## 基本结构

| file | size | top-level type | record count | key fields |
| ---- | ---: | -------------- | -----------: | ---------- |
| `card_chinese_data.json` | 117,456 bytes | `object` | 207 | `name`, `set_name`, `number`, `chinese_name`, `set_code_cn`, `card_index_cn`, `image_url`, `attacks_en`, `attacks_cn`, `abilities_en`, `abilities_cn`, `hp`, `file`, `match_score`, `match_method` |
| `card_data_cache.json` | 107,787 bytes | `object` | 207 | `name`, `set_name`, `number`, `card_type`, `img`, `hp`, `attacks`, `abilities`, `attacks_en`, `attacks_cn`, `abilities_en`, `abilities_cn` |

补充说明：

- `card_chinese_data.json` 的顶层不是记录数组，而是一个三键对象：`metadata`、`cards`、`not_found`。
- 实际记录位于 `card_chinese_data.json["cards"]`，共 207 条。
- `card_data_cache.json` 的顶层直接是以 `SET-NUMBER` 形式为 key 的对象，例如 `ASC-189`、`SSH-178`。

## 中文数据字段

`card_chinese_data.json` 已包含明显可用于中文侧检索和映射的字段：

- 中文卡名：`chinese_name`
- 基础卡名：`name`
- 系列/集合：`set_name`
- 编号：`number`
- 中文图片索引：`set_code_cn`、`card_index_cn`
- 本地文件路径：`file`
- 中文招式名列表：`attacks_cn`
- 中文特性名列表：`abilities_cn`
- 英文招式名列表：`attacks_en`
- 英文特性名列表：`abilities_en`
- 匹配元数据：`match_score`、`match_method`

结论：

- 这份文件非常适合做“卡牌定位层”和“本地文件映射层”。
- 它也适合做 prompt 的卡牌身份输入，例如卡名、set、编号、候选本地文件。
- 但它**不包含完整中文效果文本**，尤其没有 Trainer/Supporter 的整段效果描述，也没有攻击/特性的完整中文效果句子。
- 因此，它**不足以单独作为 semantic extraction prompt 的正文输入**。

## 缓存数据字段

`card_data_cache.json` 包含的是更偏“半结构化卡牌缓存”的字段：

- 基础识别字段：`name`, `set_name`, `number`
- 类型字段：`card_type`
- 资源字段：`img`, `hp`
- 结构化招式：`attacks[]`
- 结构化特性：`abilities[]`
- 中英文名称列表：`attacks_en`, `attacks_cn`, `abilities_en`, `abilities_cn`

其中可观察到的嵌套字段包括：

- `attacks[].name`
- `attacks[].damage.amount`
- `attacks[].damage.suffix`
- `attacks[].cost`
- `attacks[].effect`
- `abilities[].name`
- `abilities[].effect`
- `abilities[].type`

但也存在明显限制：

- 没有 `rules`
- 没有 `text`
- 没有 `trainer_text`
- 没有 `ops`
- 没有 `parsed_effects`
- 没有 `generated_tests`
- 没有 `cache_metadata`

额外发现：

- `card_data_cache.json` 中 207 条记录的 `card_type` 全部都是 `Pokemon`。
- 这与实际卡牌类型不一致，因为其中明确包含 Supporter，例如 `TWM145 Carmine`、`SSH178 Professor's Research`、`FLI108 Judge`、`PAL185 Iono`、`ASR150 Roxanne`。
- 因此，`card_type` 字段当前**不可信，不能直接作为后续 prompt/生成链路的类型判断依据**。

成熟度判断：

- 它不像“测试生成缓存”，因为完全没有测试或 ops 字段。
- 它也不像“已完成语义解析缓存”，因为没有 parsed effects、没有 semantic ops、没有规则级文本。
- 它最接近：
  - `D. 混合缓存`

原因：

- 它混合了基础卡牌元数据和一部分结构化攻击/特性信息；
- 但没有完整规则文本，也没有进入 semantic/test 层。

## 与本地卡牌文件映射情况

| source | total records | matched local card files | match strategy | main missing reason |
| ------ | ------------: | -----------------------: | -------------- | ------------------- |
| local `ptcg/cards/**/*.py` | 290 py files | 184 可从路径解析出 `set+number` | 目录名取 set，文件名前缀数字取 number | 104 个文件名不带编号前缀，无法仅靠路径解析 |
| `card_chinese_data.json` | 207 | 143 | `set_name + normalized(number)`；另有 `file` 可直连本地路径 | JSON 仅覆盖部分本地卡牌；未覆盖的 parseable 本地卡约 41 张 |
| `card_data_cache.json` | 207 | 143 | `set_name + normalized(number)` 或顶层 key `SET-NUMBER` | 覆盖范围与 `card_chinese_data.json` 相同，但缺少 `file` 路径字段 |
| `card_chinese_data.json` <-> `card_data_cache.json` | 207 vs 207 | 207 | `set_name + normalized(number)` | 两者记录集完全对齐，无额外差异 |

补充说明：

- `card_chinese_data.json` 的 `file` 字段 207/207 都能命中本地 `ptcg/` 下的真实文件。
- 这意味着它虽然不能单独支撑 prompt 正文，但**非常适合做“缓存记录 -> 本地卡牌文件”的桥接索引**。
- 无法匹配本地文件的主要原因不是 set/number 不可比，而是本地大量文件名本身不含数字前缀，例如：
  - `ptcg/cards/ASC/lillies_determination.py`
  - `ptcg/cards/PAF/professors_research.py`
  - `ptcg/cards/CRZ/energy_retrieval.py`

## 重点卡匹配结果

| target | local file | chinese data found | cache data found | usable for prompt |
| ------ | ---------- | ------------------ | ---------------- | ----------------- |
| `TWM145 Carmine` | `ptcg/cards/TWM/twm145carmine.py` | yes | yes | partial |
| `SSH178 Professor's Research` | `ptcg/cards/SSH/ssh178professorsresearch.py` | yes | yes | partial |
| `PAF Professor's Research` | `ptcg/cards/PAF/professors_research.py` | yes | yes | partial |
| `FLI108 Judge` | `ptcg/cards/FLI/fli108judge.py` | yes | yes | partial |
| `PAL185 Iono` | `ptcg/cards/PAL/pal185iono.py` | yes | yes | partial |
| `ASR150 Roxanne` | `ptcg/cards/ASR/asr150roxanne.py` | yes | yes | partial |

说明：

- 上述 6 张重点卡在两个 JSON 中都能找到。
- 但 `usable for prompt` 仅能标为 `partial`，因为：
  - 能定位卡牌；
  - 能拿到中文卡名、set、number；
  - 对 Pokemon 类卡牌可拿到部分攻击/特性结构；
  - 对 Supporter/Trainer 类卡牌缺少完整规则文本，无法直接生成高质量 semantic extraction prompt。

## 对后续 Phase 7/8 的影响

1. 是否还需要从 `tcg.mik.moe` 重新爬？

- 结论：`需要补爬或重新抓取文本层数据，但不一定要立刻全量重爬。`
- 原因：现有两份 JSON 在卡牌定位上已经够用，但缺少 Trainer/Supporter 的完整效果文本，难以直接支撑 prompt 语义解析。
- 更稳妥的做法是先建立规范化文本层，然后只对缺失文本或字段不可信的记录做定向补抓。

2. 是否可以直接使用现有 JSON 作为 prompt 输入？

- 结论：`不能直接作为唯一 prompt 输入源。`
- 可以作为：
  - 候选卡定位输入
  - set/number/name/file 映射输入
  - Pokemon 攻击/特性辅助输入
- 不能作为：
  - Trainer/Supporter/Item/Stadium 的完整规则文本输入
  - 最终 semantic extraction 的唯一事实来源

3. 是否需要新增一个统一的 normalized card text layer？

- 结论：`需要。`
- 原因：
  - 两份 JSON 的结构不同；
  - `card_chinese_data.json` 有本地文件路径，但缺少完整文本；
  - `card_data_cache.json` 有一些结构化攻击/特性，但类型字段不可靠；
  - 后续 prompt、ops JSON、测试生成都需要统一、可信、可追踪的文本层。

4. 推荐下一步怎么做？

- 先新增一个 `normalized card text layer` 设计，不直接改现有 JSON。
- 统一产出最小字段：
  - `set_code`
  - `number`
  - `local_file`
  - `name_zh`
  - `name_en` 或缺省
  - `card_supertype`
  - `trainer_subtype` / `pokemon_stage` / `energy_type`
  - `rules_text_zh`
  - `attacks[]`
  - `abilities[]`
  - `source provenance`
- 对现有 JSON 无法补齐 `rules_text_zh` 的卡，定向补抓 `tcg.mik.moe` 或其他稳定来源。
- 在 normalized 层完成后，再进入 semantic extraction prompt 模板设计，而不是直接对现有缓存生 prompt。

## 推荐的数据流

建议流程：

现有 JSON
-> normalized card text layer
-> semantic extraction prompt
-> semantic ops JSON
-> side-channel test generator
-> single-card PR

更细一点：

现有 `card_chinese_data.json`
-> 提供 `set/number/file/chinese_name`

现有 `card_data_cache.json`
-> 提供 `attacks/abilities` 的基础结构

补抓文本源
-> 提供 `rules_text_zh` / `trainer_text` / `effect text`

三者合并
-> normalized card text layer
-> prompt
-> semantic ops JSON
-> side-channel test

## 风险

- 字段不稳定风险：两份 JSON 结构并不完全一致，顶层组织方式也不同。
- 中文/英文名称不一致风险：部分记录只有中文名，英文名缺失或未结构化。
- set+number 匹配风险：本地文件命名并不统一，很多文件不能仅靠路径解析编号。
- 缓存过期风险：当前 207 条记录只是部分覆盖，不代表覆盖当前仓库所有卡牌。
- 缺少效果文本风险：Trainer/Supporter 缺少完整规则文本，不能直接用于语义抽取。
- 结构化字段不足风险：没有 `rules`、`text`、`ops`、`parsed_effects`、`generated_tests`。
- prompt 误判风险：如果直接拿当前缓存做 prompt，容易把 Trainer 误判为无效果或把类型判错。
- 类型字段失真风险：`card_data_cache.json` 当前 `card_type` 全量为 `Pokemon`，不能直接信任。
- 映射层断裂风险：`card_data_cache.json` 没有本地文件路径字段，单独使用时较难追溯到具体代码文件。
