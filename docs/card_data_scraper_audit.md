# Card Data Scraper Audit

## 目标

本报告用于审计现有爬取/API/缓存脚本，判断它们是否能支撑后续 `normalized card text layer` 和 `semantic extraction prompt`。

本阶段只审计现有脚本与数据生成链路，不修改任何脚本，不修改任何 JSON，不修改任何卡牌代码，不修改任何语义层代码。

## 相关数据文件

- `card_chinese_data.json`
- `card_data_cache.json`

当前问题：

- `card_chinese_data.json` 适合做卡牌定位和本地文件映射，但缺少完整 Trainer/Supporter 规则文本。
- `card_data_cache.json` 带有部分结构化字段，但当前 207 条 `card_type` 全部为 `Pokemon`，类型字段不可信。
- `card_data_cache.json` 同时缺少 `effect`、`effect_text`、`trainer_type`、`super_type`、`rule_box` 等关键字段，说明它不是由当前仓库中“按源码正确提取”的脚本完整生成的最终产物。

## 发现的脚本

| file | purpose | input source | output | data source/API | relevant |
| ---- | ------- | ------------ | ------ | --------------- | -------- |
| `scripts/fetch_chinese_card_data.py` | 为本地卡牌抓取中文名称、中文 set/card 索引和部分中文攻击/特性信息 | `ptcg/cards/**/*.py` + `card_data/*.json` 局部缓存 | `card_chinese_data.json` | `tcg.mik.moe` `card-basic-search` + `card-detail` | high |
| `scripts/fetch_deck_data.py` | 抓取热门卡组和 deck 明细，为中英 set/number 映射提供辅助数据 | 无本地输入 | `deck_data.json` | `tcg.mik.moe` deck 系列接口 | high |
| `scripts/generate_card_cache.py` | 从 Python 源码提取结构化卡牌属性，理论上可生成规范 cache | `ptcg.core.card_registry` + card classes | stdout 或自定义 `--output` | 本地源码，不调用外部 API | high |
| `scripts/download_card_images.py` | 下载中文卡图，并把图像路径/中文名写回 cache | `card_chinese_data.json` + `card_data_cache.json` | 更新 `frontend/public/cards` 与 `card_data_cache.json` | 图片 URL 来自 `tcg.mik.moe/static/img` | high |
| `scripts/backfill_card_cache.py` | 用源码回填 cache 中缺失的 effect/hp/rule_box 等字段 | `card_data_cache.json` + 本地 card classes | 更新 `card_data_cache.json` | 本地源码 | high |
| `scripts/llm_classify_cards.py` | 给 cache 追加 `effect_category` 分类 | `card_data_cache.json` + 本地源码 | 更新 `card_data_cache.json` | 本地源码 | medium |
| `scripts/verify_card_texts.py` | 校验源码文本与 API 文本一致性 | `deck_data.json` + 本地 card classes | stdout 报告 | `tcg.mik.moe` `card-detail` | high |
| `scripts/verify_card_consistency.py` | 校验 cache 与源码是否一致 | `card_data_cache.json` + 本地 card classes | stdout/文件报告 | 本地源码 | high |
| `scripts/verify_card_effects.py` | 对比 cache 与源码效果字段，识别实现缺失或缓存误报 | `card_data_cache.json` + 本地源码 AST | `.omc/state/card-effect-verification.json` | 本地源码 | high |
| `scripts/rebuild_all_cards.py` | 通过中文 setCode 重建卡牌源码 | `deck_data.json` + registry | 重写 `ptcg/cards/**/*.py` | `tcg.mik.moe` `card-detail` | medium |
| `scripts/gen_cards.py` | 从 API 明细自动生成缺失卡牌 Python 文件 | `deck_data.json` | 新建 `ptcg/cards/**/*.py` | `tcg.mik.moe` `card-detail` | medium |
| `scripts/map_missing_cards.py` | 为缺失核心卡寻找中英 setCode 映射 | `deck_data.json` + `card_data_cache.json` | stdout | `tcg.mik.moe` search/detail | medium |
| `scripts/translate_card_names.py` | 利用 `card_chinese_data.json` 把源码英文名替换成中文名 | `card_chinese_data.json` + `ptcg/cards/**/*.py` | 修改 card Python 文件 | 本地 JSON | low |

额外观察：

- `docs/CODEX.md` 提到 `refresh_card_cache.py`，但仓库中并不存在该脚本。
- 这意味着“统一刷新 `card_data_cache.json` 的 canonical 入口”在当前仓库中是缺失的。

## 数据生成链路

当前能够明确确认的链路：

`fetch_chinese_card_data.py`
-> 读取 `ptcg/cards/**/*.py`
-> 调用 `tcg.mik.moe` `card-basic-search` / `card-detail`
-> 写入 `card_chinese_data.json`

`fetch_deck_data.py`
-> 调用 `tcg.mik.moe` deck 系列接口
-> 写入 `deck_data.json`

`generate_card_cache.py`
-> 读取本地 card classes
-> 提取结构化字段
-> 输出 JSON 到 stdout 或 `--output`

`download_card_images.py`
-> 读取 `card_chinese_data.json`
-> 下载图片
-> 更新 `card_data_cache.json` 中的 `name` / `img`

`backfill_card_cache.py`
-> 读取 `card_data_cache.json`
-> 用本地源码回填 `effect` / `rule_box` / `hp` / `retreat` / `weakness` / `resistance` / `stage` / `evolve_from`
-> 再写回 `card_data_cache.json`

对 `card_data_cache.json` 的当前形态，最合理的推断链路是：

`generate_card_cache.py --output card_data_cache.json`
-> `download_card_images.py`
-> `backfill_card_cache.py`
-> 可选 `llm_classify_cards.py --apply`

但必须强调：

- 这个链路是 `inferred`，不是仓库中显式固化的单脚本流水线。
- 当前 `card_data_cache.json` 的字段形态并不能被上述现存脚本完整复现，说明中间存在历史脚本、手工转换或缺失的刷新步骤。

## 字段来源分析

| output field | source script | source API/page field | reliable | notes |
| ------------ | ------------- | --------------------- | -------- | ----- |
| `chinese_name` | `fetch_chinese_card_data.py` | `card-basic-search.list[].cardName` | medium | 来自最佳匹配候选，不是 detail 主字段 |
| `set_name` | `fetch_chinese_card_data.py` / `generate_card_cache.py` | 本地源码目录名或源码属性 | high | 依赖本地实现，稳定 |
| `number` | `fetch_chinese_card_data.py` / `generate_card_cache.py` | 本地源码属性 | high | 依赖本地实现，稳定 |
| `set_code_cn` | `fetch_chinese_card_data.py` | `card-basic-search.list[].setCode` | medium | 候选匹配结果字段 |
| `card_index_cn` | `fetch_chinese_card_data.py` | `card-basic-search.list[].cardIndex` | medium | 候选匹配结果字段 |
| `image_url` | `fetch_chinese_card_data.py` | 由 `set_code_cn + card_index_cn` 拼接 | medium | 不是 API 直接字段 |
| `attacks_cn` | `fetch_chinese_card_data.py` | `card-detail.data.pokemonAttr.attack[].name` | medium | 仅适用于 Pokemon |
| `abilities_cn` | `fetch_chinese_card_data.py` | `card-detail.data.pokemonAttr.ability[].name` | medium | 仅适用于 Pokemon |
| `file` | `fetch_chinese_card_data.py` | 本地源码路径 | high | 通过 AST 扫描本地卡牌文件获得 |
| `match_score` | `fetch_chinese_card_data.py` | 本地评分逻辑 | medium | 非上游字段，依赖当前匹配算法 |
| `match_method` | `fetch_chinese_card_data.py` | 本地评分逻辑 | medium | 非上游字段，依赖当前匹配算法 |
| `name` in cache | 现有 cache 形态不明；`generate_card_cache.py` / `download_card_images.py` 都可能写 | 本地源码 `inst.name` 或中文 JSON `chinese_name` | low | 当前 cache 为中文名，不能证明来源唯一 |
| `card_type` in cache | `generate_card_cache.py` 理应写；当前文件实际来源不明 | 本地类类型或上游 `cardType` | low | 当前文件 207/207 全为 `Pokemon`，明显不可信 |
| `img` in cache | `download_card_images.py` | `image_url` -> 本地 `/cards/...png` 或外链图片 URL | medium | 当前 cache 仍多为外链 URL，不像下载后本地路径状态 |
| `attacks[].effect` | `fetch_chinese_card_data.py` / `backfill_card_cache.py` | API `pokemonAttr.attack[].text` 或源码 `Attack.text` | low | 当前 fetch 脚本误读 `effect` 字段，实际很可能拿不到 |
| `abilities[].effect` | `fetch_chinese_card_data.py` / `backfill_card_cache.py` | API `pokemonAttr.ability[].text` 或源码 `Ability.text` | low | 同上，字段名疑似错用 |
| `effect_text` | `generate_card_cache.py` | `inst.text` | high | 但当前 `card_data_cache.json` 中完全不存在 |

## card_type 全部为 Pokemon 的原因分析

最可能原因：

- **当前根目录 `card_data_cache.json` 不是由现存 `generate_card_cache.py` 独立生成的结果，而是历史旧缓存或缺失脚本产物。**

证据：

1. 当前 `card_data_cache.json` 中：
   - `total = 207`
   - `card_type == "Pokemon"` 的记录也是 `207`
   - `Trainer` / `Energy` 数量都是 `0`
   - `effect` / `effect_text` / `attack_effect` / `ability_effect` 数量都是 `0`

2. 现存 `generate_card_cache.py` 明确会按源码类型输出：
   - Pokemon -> `card_type = "Pokemon"`
   - Energy -> `card_type = "Energy"`
   - Supporter/Item/Tool/Stadium -> `card_type = "Trainer"`
   - 且训练家卡会写 `effect_text`

3. 当前实际 cache 中：
   - `SSH-178` / `TWM-145` / `PAL-185` / `FLI-108` / `ASR-150` 都是 `card_type = "Pokemon"`
   - 这些卡在源码里都继承 `SupporterCard`
   - 因此当前 cache 不可能是由 `generate_card_cache.py` 直接完整生成的结果

4. `download_card_images.py` 会直接写回 cache，但它：
   - 只更新 `name` / `img`
   - 对新建条目默认写 `card_type = card_type or "Unknown"`
   - `fetch_chinese_card_data.py` 又并不产出 `card_type`
   - 所以它不会把全量条目统一改成 `Pokemon`

5. `backfill_card_cache.py` 会回填 effect/hp 等字段，但它不会批量重写 `card_type`

6. `llm_classify_cards.py` 只会追加 `effect_category`，也不会改 `card_type`

7. 当前 cache 同时包含：
   - `attacks_en`
   - `attacks_cn`
   - `abilities_en`
   - `abilities_cn`
   但现存仓库中并没有一个脚本会把这组字段完整写入 `card_data_cache.json`。
   这进一步说明当前 cache 很可能来自历史脚本或手工转换流程，而不是现存链路的直接产物。

对“是不是脚本 bug”的判断：

- 不是 `generate_card_cache.py` 的直接 bug。
- 更像是：
  - 历史生成脚本缺失；
  - 多步合并链路未在仓库中固化；
  - 或当前根目录 cache 是旧版本产物，与现有脚本已脱节。

是否能修复：

- 能修，但不建议直接在当前旧 cache 上做补丁式修修补补。
- 更合理的方案是：
  - 保留现有 JSON 不动；
  - 明确新的 normalized 生成链路；
  - 用现有脚本重新生成一个可复现的新输出。

修复后影响：

- 如果直接覆盖当前 `card_data_cache.json`，可能影响：
  - `verify_card_consistency.py`
  - `verify_card_effects.py`
  - `ptcgbench/agents/tools/card_query.py`
  - 任何依赖现有字段命名和中文名形态的工具
- 因此修复更适合通过新 `normalized` 输出落地，而不是原地覆盖旧 cache。

## 完整规则文本缺口

现有脚本是否能抓到完整文本：

- Trainer/Supporter 完整规则文本：`能`
  - 证据：`gen_cards.py` 和 `verify_card_texts.py` 都直接读取 `api_data["description"]`
  - 说明 `tcg.mik.moe` detail 接口本身提供了 Trainer/Supporter 文本

- Item/Stadium 完整规则文本：`能`
  - 同样来自 `api_data["description"]`

- 攻击/特性完整中文效果文本：`理论上能，但现有抓取脚本字段名用错了`
  - `gen_cards.py` / `verify_card_texts.py` 读取的是 `attack[].text` / `ability[].text`
  - `fetch_chinese_card_data.py` 读取的是 `attack[].effect` / `ability[].effect`
  - 这两个脚本对同一 API 结构使用了不同字段名
  - 从仓库消费侧看，`text` 更像是正确字段，`effect` 很可能是错误或旧版字段名

当前脚本已经能拿到但没有保存的字段：

- `rules_text_zh` / `trainer_text` / `card text`
  - `tcg.mik.moe` detail 的 `description`
  - 当前没有被 `fetch_chinese_card_data.py` 或 `card_data_cache.json` 保存为稳定字段

- `rules_text_en`
  - 现有脚本中未见稳定抓取保存路径
  - 需要确认 `tcg.mik.moe` 是否提供英文 description；当前代码未使用

- `attacks[].effect` 中文 / `abilities[].effect` 中文
  - API 很可能有，但当前 `fetch_chinese_card_data.py` 字段名读取错误，导致没有稳定落盘

- `trainer/supporter/item/stadium` 的完整效果文本
  - API 已有 `description`
  - 但当前 JSON 生成链路没有把它沉淀为后续 prompt 可直接用的规范字段

如果现有脚本拿不到或未保存，需要怎么补：

1. 主要补抓源：
   - 首选 `tcg.mik.moe` `card-detail`

2. `tcg.mik.moe` 是否可能提供：
   - 很可能能提供 Trainer/Supporter/Item/Stadium 的完整中文规则文本
   - 现有脚本已经证明 `description` 可用

3. 现有脚本是否已有图片 URL 或页面定位信息：
   - 有
   - `card_chinese_data.json` 已保存 `set_code_cn`、`card_index_cn`、`image_url`
   - `deck_data.json` 也保存 `setCode` / `cardIndex` / `setCodeEn` / `cardIndexEn`

4. 是否需要新增 `source provenance` 字段：
   - 需要
   - 至少记录：
     - 来源脚本
     - API endpoint
     - set/card index
     - fetched_at
     - matched_by / match_score

5. 是否需要新增 normalized 层而不是直接改原 JSON：
   - 需要
   - 这是当前最稳妥的方向

## 是否需要重新爬 tcg.mik.moe

1. 是否需要全量重爬

- `不建议第一步就全量重爬`
- 因为现有 `card_chinese_data.json` 已足够承担定位/索引工作
- 真正缺的是文本层，不是基础映射层

2. 是否可以定向补抓缺字段

- `可以，而且更推荐`
- 重点补：
  - `description`
  - `cardType`
  - trainer subtype
  - `attack[].text`
  - `ability[].text`

3. 是否应该优先补 Trainer/Supporter 文本

- `应该`
- 因为当前缺口最大、又直接影响后续 semantic extraction prompt 的，是 Trainer/Supporter/Item/Stadium 的规则文本

4. 是否应该保留现有 JSON 不动，另建 normalized 输出

- `应该`
- 当前旧 JSON 已被多个工具消费，直接覆盖风险高

## 推荐下一步

- 不直接修改现有 `card_chinese_data.json` 和 `card_data_cache.json`
- 新增一个 `normalized card text layer`
- 把现有 JSON 当作：
  - 定位层
  - 索引层
  - 本地文件映射层
- 对缺失文本做定向补抓，优先 `tcg.mik.moe/card-detail`
- 统一保存：
  - `set_code`
  - `number`
  - `local_file`
  - `name_zh`
  - `name_en`
  - `card_supertype`
  - `trainer_subtype`
  - `rules_text_zh`
  - `rules_text_en`（若源可得）
  - `attacks[]`
  - `abilities[]`
  - `source provenance`
- 明确新的可复现流水线，而不是继续依赖不完整的历史 cache

## 风险

- 上游页面/API 变化：`description`、`pokemonAttr`、`attack[].text` 字段可能调整
- 中文字段缺失：部分卡可能只有名称映射，没有完整文本
- 类型字段错误：旧 cache 当前 `card_type` 全量失真
- 本地文件映射错误：路径命名和 set/number 并不总是一致
- 缓存污染：多个脚本对同一 `card_data_cache.json` 回写，容易产生混合状态
- 直接覆盖原 JSON 的风险：会影响现有校验、Agent 工具和历史假设
- prompt 使用不完整文本导致误判：尤其是 Trainer/Supporter 文本缺失时最危险
- 字段名错位风险：同一 API 在不同脚本中被当成 `text` 或 `effect` 使用
- 文档与脚本脱节风险：`docs/CODEX.md` 提到的 `refresh_card_cache.py` 实际不存在
