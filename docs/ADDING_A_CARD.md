# 添加新卡牌指南

> 从卡牌数据获取、文件生成、代码实现到测试验证的完整流程。
> **预估时间**: 10-30 分钟（简单卡牌） / 1-2 小时（复杂卡牌）

---

## 目录

- [1. 准备工作](#1-准备工作)
- [2. 确定卡牌类型](#2-确定卡牌类型)
- [3. 编写卡牌文件](#3-编写卡牌文件)
- [4. 各类型卡牌模板](#4-各类型卡牌模板)
- [5. 编写测试](#5-编写测试)
- [6. 验证清单](#6-验证清单)
- [7. 常见问题](#7-常见问题)

---

## 1. 准备工作

### 前置信息

添加卡牌前需要确认：

1. **卡牌所属扩展包** — 即 set code（如 `SSP`、`PAL`、`SVI`）
2. **卡牌编号** — 卡牌在该系列中的序号（如 `130`）
3. **卡牌名称** — 中英文名
4. **卡牌类型** — Pokemon / Trainer (Supporter/Item/Stadium/Tool) / Energy
5. **效果文字** — 卡牌上印的效果描述文本

### 创建目录

如果目标系列目录还不存在：

```bash
mkdir -p ptcg/cards/{SET_CODE}/
touch ptcg/cards/{SET_CODE}/__init__.py
```

---

## 2. 确定卡牌类型

根据卡牌效果选择正确的基类：

| 卡牌类型 | 基类 | 文件位置 |
|---------|------|---------|
| 基础宝可梦 | `PokemonCard` | `ptcg/core/card.py` |
| 进化宝可梦（Stage 1） | `PokemonCard` （stage=STAGE_1） | `ptcg/core/card.py` |
| 进化宝可梦（Stage 2） | `PokemonCard` （stage=STAGE_2） | `ptcg/core/card.py` |
| 支援者 | `SupporterCard` | `ptcg/core/card.py` |
| 物品 | `ItemCard` | `ptcg/core/card.py` |
| 宝可梦道具 | `ItemCard` （trainerType=TOOL） | `ptcg/core/card.py` |
| 场地 | `StadiumCard` | `ptcg/core/card.py` |
| 基本能量 | `BasicEnergyCard` | `ptcg/core/card.py` |
| 特殊能量 | `SpecialEnergyCard` | `ptcg/core/card.py` |
| 宝可梦 V | `PokemonCard` （pokemonRule=V） | `ptcg/core/card.py` |
| 宝可梦 ex | `PokemonCard` （pokemonRule=NONE, prize=2） | `ptcg/core/card.py` |

### 名词对照

| 属性 | 枚举类型 | 常见值 |
|------|---------|-------|
| 属性 | `CardType` | `FIRE`, `WATER`, `GRASS`, `LIGHTNING`, `PSYCHIC`, `FIGHTING`, `DARK`, `METAL`, `DRAGON`, `COLORLESS`, `NONE` |
| 进化阶段 | `Stage` | `BASIC`, `STAGE_1`, `STAGE_2` |
| 位置 | `PokemonPosition` | `ACTIVE`, `BENCH`, `NONE` |
| 能力类型 | `AbilityType` | `ACTIVE`, `PASSIVE`, `INSTANT` |
| 能力触发 | `AbilityTrigger` | `ATTACKING`, `ATTACKED`, `RETREAT`, `OTHER` |

---

## 3. 编写卡牌文件

### 文件命名规则

```
ptcg/cards/{SET_CODE}/{set_code_lower}{number}{英文名去特殊字符小写}.py
```

例如：`SSP` 系列第 `130` 号 `Archaludon ex` → `ptcg/cards/SSP/ssp130archaludonex.py`

### 类命名规则

```
{SET_CODE大写}{number}{英文名去特殊字符}PascalCase
```

例如：`SSP130Archaludonex`

### 卡牌文件基本结构

```python
"""Card name - SET NUM"""
from ptcg.core.card import PokemonCard  # 或 SupporterCard / ItemCard
from ptcg.core.action import AttackAction, PlayPokemonAction  # 需要的动作类型
from ptcg.core.attack import Attack      # 攻击定义（宝可梦卡需要）
from ptcg.core.enums import CardType, PokemonType, Stage, PokemonPosition, AbilityType, AbilityTrigger
from ptcg.core.reducer import reduce_attack_action  # 需要的 reducer
from ptcg.utils.utils import check_energy, opponent_active, move_cards, current_player


class {ClassName}(PokemonCard):
    """中文名称 - 卡牌类型. HP: xxx."""
    def __init__(self) -> None:
        super().__init__()
        # === 基础属性 ===
        self.set_name = "{SET_CODE}"
        self.number = "{NUM}"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "中文卡名"
        # === 宝可梦属性 ===
        self.hp = xxx
        self.cardType = CardType.xxx
        self.stage = Stage.xxx
        self.evolveFrom = ['进化来源名称']
        self.prize = 1  # 普通卡=1, ex/V=2
        self.retreat = [CardType.COLORLESS] * n
        self.weakness = [CardType.xxx]
        self.resistance = [CardType.xxx]  # 或无抵抗则空列表
        # === 攻击 ===
        self.attacks = [
            Attack({"name": "攻击名", "damage": n, "cost": [CardType.xxx], "text": "效果文本"})
        ]
        # === 特性（可选） ===
        self.ability = [
            InstantAbility({
                "name": "特性名",
                "abilityType": AbilityType.INSTANT_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "text": "特性效果描述"
            })
        ]

    def get_actions(self, state):
        """返回合法动作列表"""
        actions = []
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))
        return actions

    def reduce_action(self, action, state):
        """执行动作"""
        if isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
        elif isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
```

---

## 4. 各类型卡牌模板

### 4.1 支援者卡模板

```python
from ptcg.core.card import SupporterCard
from ptcg.core.action import UseSupporterAction
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class {SET_CODE}{NUM}{Name}(SupporterCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "{SET_CODE}"
        self.number = "{NUM}"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "中文名"
        self.cardType = CardType.NONE
        self.text = "效果描述"

    def get_actions(self, state):
        player = current_player(state)
        actions = []
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            # ==== 在这里实现卡牌效果 ====
            # 示例：抽牌
            move_cards(
                player.deck[0],
                (player.id, CardPosition.DECK),
                (player.id, CardPosition.HAND),
                state,
            )
            player.supporterPlayedTurn = True
```

### 4.2 物品卡模板

```python
from ptcg.core.card import ItemCard
from ptcg.core.action import UseItemAction
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class {SET_CODE}{NUM}{Name}(ItemCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "{SET_CODE}"
        self.number = "{NUM}"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "中文名"
        self.cardType = CardType.NONE
        self.text = "效果描述"

    def get_actions(self, state):
        actions = []
        actions.append(UseItemAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            # 实现效果
            pass
```

### 4.3 能量卡模板

```python
from ptcg.core.card import BasicEnergyCard
from ptcg.core.enums import CardType


class {SET_CODE}{NUM}{Name}(BasicEnergyCard):
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "{SET_CODE}"
        self.number = "{NUM}"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "中文能量名"
        self.cardType = CardType.xxx  # 对应能量属性
```

---

## 5. 编写测试

### 自动生成测试

运行全量测试生成脚本：

```bash
# 如果已有测试模板脚本
uv run python scripts/test_templates.py
```

### 手动运行测试

```bash
# 全量测试回归
uv run python -m pytest tests/ -q

# 仅测试 cards 相关
uv run python -m pytest tests/cards/generated/ -q

# 查看测试覆盖
uv run python -m pytest tests/ -q --coverage  # 如已配置
```

### 测试层级说明（L1-L6）

| 层级 | 覆盖内容 | 生成方式 |
|------|---------|---------|
| L1 | 卡牌属性正确性（名称、HP、类型等） | 自动 |
| L2 | get_actions 返回正确动作 | 自动 |
| L3 | reduce_action 基础效果执行 | 自动 |
| L4 | 边界条件（空牌库、满备战区等） | 自动/手动 |
| L5 | 组合效果（进化解禁、效果叠加等） | 手动 |
| L6 | 完整游戏交互流程 | 手动 |

---

## 6. 验证清单

提交前逐项确认：

- [ ] 卡牌文件存在于 `ptcg/cards/{SET}/` 下
- [ ] 类名遵循 `{SET_CODE}{NUM}{Name}` PascalCase 命名规则
- [ ] `self.id = f"{self.set_name}-{self.number}"` 按格式拼接
- [ ] `super().__init__()` 在 `__init__` 中正确调用
- [ ] 不使用 `from x import *`（显式导入所需函数）
- [ ] 所有导入的模块确实存在且路径正确
- [ ] `get_actions()` 返回的动作来自 `info["raw_available_actions"]` 或自行构造的标准动作
- [ ] `reduce_action()` 正确处理所有 `isinstance` 分支
- [ ] Generator 多步操作使用 `yield from` 而非阻塞调用
- [ ] 不使用裸 `except StopIteration: pass`（使用 `SafeStepGenerator`）
- [ ] `uv run python -m pytest tests/ -q` 全绿
- [ ] 对应扩展包目录有 `__init__.py`（可为空文件）

---

## 7. 常见问题

### Q: 卡牌效果太复杂，现有原语不够用怎么办？

A: 在 `reduce_action()` 中直接操作 `state` 对象实现自定义逻辑。常用操作：
- `move_cards()` 进行卡牌位置转移
- `state.player1.hand` / `state.player2.deck` 直接访问区域
- `judge_termination(state)` 检查游戏是否结束
- `next_turn(state)` 手动结束回合

### Q: 新增系列需要做哪些事？

A: 1) 创建 `ptcg/cards/{SET}/__init__.py`（空文件）；2) 添加各卡牌文件；3) 确认 `CardRegistry` 的 rglob 能扫描到（无需额外配置）

### Q: 如何验证卡牌属性与官方数据一致？

A: 运行 `uv run python scripts/verify_card_consistency.py`（需要先有 `card_data_cache.json`）

### Q: 卡牌效果涉及抛硬币怎么办？

A: 使用 `flip_coin(state)` 获取 Coin.HEAD / Coin.TAIL，然后根据结果分支处理：

```python
from ptcg.utils.utils import flip_coin

result = flip_coin(state)
if result == Coin.HEAD:
    # 正面效果
else:
    # 反面效果
```

### Q: `move_cards()` 各参数怎么填？

A: 参数格式为 `(PlayerId, CardPosition)`：
- 玩家标识：`player.id` 或 `opponent.id`（通过 `current_player(state)` / `opponent_player(state)` 获取）
- 位置枚举：`CardPosition.HAND`、`CardPosition.DECK`、`CardPosition.DISCARD`、`CardPosition.ACTIVE`、`CardPosition.BENCH`、`CardPosition.PRIZE`、`CardPosition.LOST_ZONE`

---

> **相关文档**: `ptcg/core/AGENTS.md`（引擎核心）、`ptcg/cards/AGENTS.md`（卡牌实现）、`ptcg/utils/AGENTS.md`（工具函数）
