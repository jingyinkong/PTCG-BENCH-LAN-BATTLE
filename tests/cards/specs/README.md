# Card Effect Specs

Tier 3 卡牌效果规格定义。每个 spec 是该卡的完整行为契约。

## Spec 格式

```json
{
  "card_id": "SET-NNN",
  "name": "卡牌名称",
  "text_rules": ["规则文本"],
  "scenarios": [{"name": "场景", "expected": {...}}]
}
```

## 已完成的样本 (5张)

1. paf-079-electric-generator.json — 电气发生器
2. pre-106-earthen-vessel.json — 大地容器
3. sit-156-forest-seal-stone.json — 森林封印石
4. obf-125-charizard-ex.json — 喷火龙ex
5. svi-080-miraidon-ex.json — 密勒顿ex
