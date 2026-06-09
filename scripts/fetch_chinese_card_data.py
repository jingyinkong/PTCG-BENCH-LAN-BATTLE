#!/usr/bin/env python3
"""
异步并发从 tcg.mik.moe API 抓取卡片中文数据。
用法: uv run python scripts/fetch_chinese_card_data.py [-c 20]

匹配策略: 调用 card-detail API，通过 setCodeEn + cardIndexEn 精确匹配
          Python 卡片定义中的 set_name + number，淘汰不可靠的名称搜索+results[0]回退。
"""
import argparse
import asyncio
import ast
import json
import sys
import time
from pathlib import Path

import aiohttp

TCG_API_SEARCH = "https://tcg.mik.moe/api/v3/card/card-basic-search"
TCG_API_DETAIL = "https://tcg.mik.moe/api/v3/card/card-detail"
IMAGE_BASE = "https://tcg.mik.moe/static/img"
CARDS_DIR = Path(__file__).parent.parent / "ptcg" / "cards"
OUTPUT_FILE = Path(__file__).parent.parent / "card_chinese_data.json"
DATA_DIR = Path(__file__).parent.parent / "card_data"

DEFAULT_CONCURRENCY = 15
DEFAULT_TIMEOUT = 10
DETAIL_TIMEOUT = 10
MIN_MATCH_SCORE = 20


def _normalize_number(n: str | int | None) -> str:
    """标准化卡牌编号：去前导零，统一比较。086 → 86, 86 → 86"""
    if n is None:
        return ""
    try:
        return str(int(str(n)))
    except (ValueError, TypeError):
        return str(n).strip().lstrip("0") or str(n).strip()


def extract_card_info(file_path: Path) -> dict | None:
    """从 Python 卡片文件中提取名称、编号、HP、攻击、特性。"""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None

    set_name = file_path.parent.name
    card_name = None
    card_number = None
    hp = None
    attacks = []
    abilities = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if not (isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"):
                continue

            if not isinstance(node.value, ast.Constant):
                continue

            attr = target.attr
            val = node.value.value

            if attr == "name" and card_name is None:
                card_name = val
            elif attr == "number":
                card_number = val
            elif attr == "hp":
                hp = val

    # 提取 Attack/Ability 构造调用中的 name 参数
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = getattr(node.func, "id", "")
            if fn == "Attack":
                attack_info = _extract_kwargs(node)
                if "name" in attack_info:
                    attacks.append(attack_info)
            elif "Ability" in fn:
                ability_info = _extract_kwargs(node)
                if "name" in ability_info:
                    abilities.append(ability_info)

    return {
        "name": card_name,
        "set_name": set_name,
        "number": str(card_number) if card_number is not None else "",
        "hp": hp,
        "attacks": attacks,
        "abilities": abilities,
        "file": str(file_path.relative_to(CARDS_DIR.parent)),
        "search_terms": _build_search_terms(card_name, file_path),
    } if card_name else None


def _build_search_terms(card_name: str, file_path: Path) -> list:
    """生成备选搜索词列表。文件名推算英文名作为兜底。"""
    terms = [card_name]
    stem = file_path.stem.replace("_", " ").replace("-", " ")
    if stem.lower() != card_name.lower():
        terms.append(stem)
    # 如果是英文名卡片，也搜原名
    if any(ord(c) < 128 for c in card_name):
        terms.insert(0, card_name)
    return terms


def _extract_kwargs(node: ast.Call) -> dict:
    """从 AST Call 节点提取关键字参数为 dict。"""
    result = {}
    for kw in getattr(node, "keywords", []):
        if isinstance(kw.value, ast.Constant):
            result[kw.arg] = kw.value.value
        elif isinstance(kw.value, ast.Dict):
            # 处理嵌套字典（如 damage: {amount: 190, suffix: ""}）
            nested = {}
            for k, v in zip(kw.value.keys, kw.value.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                    nested[k.value] = v.value
            result[kw.arg] = nested
    return result


def _compute_match_score(card: dict, detail: dict) -> tuple[int, str]:
    """综合评分匹配：结构比对（数值跨国界）+ 集合码 + 名称相似度。

    评分维度：
    - setCodeEn+cardIndexEn 精确匹配: +100（最高优先级）
    - 结构签名匹配（HP/攻击伤害/攻击数/特性数）: +45
    - 英文名相似度（文件茎 vs nameEn）: +25
    - 训练家/能量卡同名: +50
    """
    score = 0
    reasons = []

    # ── 1. 精确集合码匹配 ──
    api_set_en = (detail.get("setCodeEn") or "").upper()
    api_idx_en = _normalize_number(detail.get("cardIndexEn"))
    card_set = (card.get("set_name") or "").upper()
    card_num = _normalize_number(card.get("number"))

    if api_set_en == card_set and api_idx_en == card_num:
        score += 100
        reasons.append("setCodeEn+cardIndexEn 精确匹配")
    elif api_set_en == card_set:
        score += 40
        reasons.append(f"setCodeEn 匹配 (编号: api={api_idx_en} card={card_num})")

    # ── 2. effectSameCards 跨系列匹配 ──
    same_cards = detail.get("effectSameCards", [])
    if isinstance(same_cards, str):
        try:
            same_cards = json.loads(same_cards)
        except Exception:
            same_cards = []
    for sc in same_cards:
        sc_set = (sc.get("setCodeEn") or "").upper()
        sc_idx = _normalize_number(sc.get("cardIndexEn"))
        if sc_set == card_set and sc_idx == card_num:
            score += 90
            reasons.append("effectSameCards 匹配")
            break

    # ── 3. 英文名相似度 ──
    file_stem = Path(card.get("file", "")).stem.replace("_", " ").replace("-", " ")
    api_name_en = (detail.get("nameEn") or "").lower()
    name_en_words = set(api_name_en.replace(" ex", "").split())
    stem_words = set(file_stem.lower().replace(" ex", "").split())
    overlap = name_en_words & stem_words
    if overlap:
        score += 25
        reasons.append(f"英文名匹配: {overlap}")
    elif file_stem.lower() in api_name_en or api_name_en in file_stem.lower():
        score += 20
        reasons.append(f"英文名子串匹配: {file_stem} ↔ {api_name_en}")

    # ── 4. 训练家/能量卡 ──
    card_type = detail.get("cardType", "")
    if card_type in ("Supporter", "Item", "Stadium", "Tool", "Energy", "Trainer"):
        if (card.get("name") or "").strip() == (detail.get("name") or "").strip():
            score += 50
            reasons.append(f"{card_type}卡名称匹配")

    # ── 5. 宝可梦结构签名匹配（数值跨国界，不依赖名称字符串）──
    try:
        pokemon_attr = detail.get("pokemonAttr")
        if isinstance(pokemon_attr, str):
            pokemon_attr = json.loads(pokemon_attr)
    except Exception:
        pokemon_attr = {}

    if pokemon_attr and card_type == "Pokemon":
        # HP 值匹配
        api_hp = pokemon_attr.get("hp")
        card_hp = card.get("hp")
        if api_hp is not None and card_hp is not None:
            if api_hp == card_hp:
                score += 20
                reasons.append(f"HP匹配({api_hp})")
            else:
                score -= 10  # HP 不同惩罚（可能不同卡）

        # 攻击数量匹配
        api_attacks = pokemon_attr.get("attack") or []
        card_attacks = card.get("attacks") or []
        if len(api_attacks) == len(card_attacks) and len(card_attacks) > 0:
            score += 10
            reasons.append(f"攻击数匹配({len(card_attacks)})")

        # 攻击伤害值匹配（数值跨国界）
        api_damages = sorted([int(str(a.get("damage", "0")).replace("+","").replace("×","") or "0") for a in api_attacks])
        card_damages = sorted([int(str(ca.get("damage", ca.get("amount", "0"))).replace("+","").replace("×","") or "0") for ca in card_attacks])
        damage_match = 0
        for cd in card_damages:
            if cd > 0 and cd in api_damages:
                damage_match += 1
        if damage_match > 0:
            score += 10 * damage_match
            reasons.append(f"伤害值匹配({damage_match}个)")

        # 特性数量匹配
        api_abilities = pokemon_attr.get("ability") or []
        card_abilities = card.get("abilities") or []
        if len(api_abilities) == len(card_abilities) and len(card_abilities) > 0:
            score += 10
            reasons.append(f"特性数匹配({len(card_abilities)})")

        # 能量类型匹配
        api_energy = pokemon_attr.get("energyType", "")
        if api_energy:
            score += 5
            reasons.append("卡牌类型一致")

        # 撤退费用匹配
        api_retreat = pokemon_attr.get("retreatCost")
        card_retreat = card.get("retreat")  # 可能在 AST 提取中
        if api_retreat is not None and card_retreat is not None and api_retreat == len(card_retreat) if isinstance(card_retreat, list) else api_retreat == card_retreat:
            score += 5
            reasons.append("撤退费用匹配")

    return score, "; ".join(reasons) if reasons else "无匹配"


async def fetch_one(session: aiohttp.ClientSession, card: dict,
                    timeout: int, sem: asyncio.Semaphore) -> dict | None:
    """异步获取单张卡片的中文数据。两步：搜索 → 详情匹配。
    支持多搜索词尝试：先用卡片名称，失败则用文件名推论搜索词。"""
    card_name = card["name"]
    # 用 file 路径做唯一键（避免同名不同卡互相覆盖，如两张"光辉喷火龙"）
    safe_name = card["file"].replace("/", "_").replace(".py", "")

    # 检查缓存
    card_file = DATA_DIR / f"{safe_name}.json"
    if card_file.exists():
        try:
            cached = json.loads(card_file.read_text(encoding="utf-8"))
            if cached.get("status") == "ok":
                return cached["data"]
        except Exception:
            pass

    search_terms = card.get("search_terms", [card_name])

    async with sem:
        all_results = []
        tried_terms = []

        for term in search_terms[:3]:  # 最多试 3 个搜索词
            try:
                async with session.post(
                    TCG_API_SEARCH,
                    json={"SearchText": term, "PageSize": 8, "Page": 1},
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    if data.get("code") != 200 or not data["data"].get("list"):
                        continue
                results = data["data"]["list"]
                tried_terms.append(term)
                # 合并所有搜索词的结果，用 effectId 去重
                seen = {r.get("effectId","") for r in all_results}
                for r in results:
                    if r.get("effectId","") not in seen:
                        all_results.append(r)
                        seen.add(r.get("effectId",""))
            except Exception:
                continue

        if not all_results:
            _save_cache(card_file, "not_found", None)
            return None

        # 按 effectId 分组去重，减少详情 API 调用量
        seen_effects = set()
        unique_results = []
        for r in all_results:
            eid = r.get("effectId", "")
            if eid and eid in seen_effects:
                continue
            seen_effects.add(eid)
            unique_results.append(r)

        # Step 2: 为每个候选结果调用详情 API
        best_match = None
        best_score = -1
        best_detail = None

        for candidate in unique_results[:5]:
            sc = candidate.get("setCode", "")
            ci = candidate.get("cardIndex", "")
            if not sc or not ci:
                continue

            try:
                async with session.post(
                    TCG_API_DETAIL,
                    json={"setCode": sc, "cardIndex": ci},
                    timeout=aiohttp.ClientTimeout(total=DETAIL_TIMEOUT),
                ) as detail_resp:
                    if detail_resp.status != 200:
                        continue
                    detail_data = await detail_resp.json()
                    if detail_data.get("code") != 200:
                        continue
                    detail = detail_data["data"]

                score, reason = _compute_match_score(card, detail)
                if score > best_score:
                    best_score = score
                    best_match = candidate
                    best_detail = detail
                    # 精确匹配到 setCodeEn+number 立即退出
                    if score >= 100:
                        break
            except Exception:
                continue

        if best_match is None or best_score < MIN_MATCH_SCORE:
            _save_cache(card_file, "not_found", {
                "card_name": card_name,
                "set_name": card.get("set_name", ""),
                "number": card.get("number", ""),
                "candidates": len(unique_results),
                "best_score": best_score,
            })
            return None

        set_code_cn = best_match.get("setCode", "")
        card_index_cn = best_match.get("cardIndex", "")
        cn_name = best_match.get("cardName", "")

        # 提取完整的攻击和特性详情（名称+伤害+费用+效果文本）
        attacks_cn = []
        attacks_detail = []
        abilities_cn = []
        abilities_detail = []
        try:
            pa = best_detail.get("pokemonAttr")
            if isinstance(pa, str):
                pa = json.loads(pa)
            if pa:
                for atk in (pa.get("attack") or []):
                    attacks_cn.append(atk.get("name", ""))
                    dmg = atk.get("damage", "0")
                    if isinstance(dmg, dict):
                        dmg_val = dmg
                    else:
                        dmg_val = {"amount": int(str(dmg).replace("+","").replace("×","") or "0"), "suffix": str(dmg)}
                    attacks_detail.append({
                        "name": atk.get("name", ""),
                        "damage": dmg_val,
                        "cost": atk.get("cost", []),
                        "effect": atk.get("effect", ""),
                    })
                for abi in (pa.get("ability") or []):
                    abilities_cn.append(abi.get("name", ""))
                    abilities_detail.append({
                        "name": abi.get("name", ""),
                        "effect": abi.get("effect", ""),
                        "type": abi.get("type", ""),
                    })
        except Exception:
            pass

        result = {
            "name": card_name,
            "set_name": card.get("set_name", ""),
            "number": card.get("number", ""),
            "chinese_name": cn_name,
            "set_code_cn": set_code_cn,
            "card_index_cn": card_index_cn,
            "image_url": f"{IMAGE_BASE}/{set_code_cn}/{card_index_cn}.png",
            "attacks_en": [a.get("name", "") for a in (card.get("attacks") or [])],
            "attacks_cn": attacks_cn,
            "attacks": attacks_detail,
            "abilities_en": [a.get("name", "") for a in (card.get("abilities") or [])],
            "abilities_cn": abilities_cn,
            "abilities": abilities_detail,
            "hp": card.get("hp"),
            "file": card["file"],
            "match_score": best_score,
            "match_method": "setCodeEn+cardIndexEn" if best_score >= 100 else "attribute_match",
        }
        _save_cache(card_file, "ok", result)
        return result


def _save_cache(path: Path, status: str, data: dict | None):
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"status": status, "data": data}
    path.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")


async def run(cards: list, concurrency: int, timeout: int):
    """主异步函数。"""
    sem = asyncio.Semaphore(concurrency)
    connector = aiohttp.TCPConnector(limit=concurrency + 10, limit_per_host=concurrency + 5)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_one(session, card, timeout, sem) for card in cards]
        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            result = await coro
            pct = (i + 1) * 100 // len(tasks)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            elapsed = time.time() - _start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(tasks) - i - 1) / rate if rate > 0 else 0
            label = result["chinese_name"] if result else "未找到"
            sys.stderr.write(f"\r  [{bar}] {pct:3d}% ({i+1}/{len(tasks)}) "
                             f"| {elapsed:.0f}s | {rate:.1f}张/s | 剩余~{eta:.0f}s | {label}")
            results.append(result)
        sys.stderr.write("\n")
    return results


_start_time: float = 0


def main():
    parser = argparse.ArgumentParser(description="异步并发抓取卡片中文数据")
    parser.add_argument("-c", "--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help=f"并发数（默认 {DEFAULT_CONCURRENCY}）")
    parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"请求超时秒数（默认 {DEFAULT_TIMEOUT}s）")
    parser.add_argument("--no-cache", action="store_true", help="重新抓取，忽略缓存")
    args = parser.parse_args()

    global _start_time
    _start_time = time.time()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PTCG 卡片中文数据抓取（asyncio 异步并发）")
    print(f"并发: {args.concurrency} | 超时: {args.timeout}s | 缓存: {DATA_DIR}")
    print("=" * 60)

    # Step 1: 扫描
    print("\n[Step 1] 扫描卡片文件...")
    all_cards = []
    for pf in sorted(CARDS_DIR.rglob("*.py")):
        if pf.name.startswith("__"):
            continue
        info = extract_card_info(pf)
        if info:
            all_cards.append(info)

    if args.no_cache:
        for f in DATA_DIR.glob("*.json"):
            f.unlink()
        cards = all_cards
        cached = 0
    else:
        cards = []
        for c in all_cards:
            safe = c["file"].replace("/", "_").replace(".py", "")
            cf = DATA_DIR / f"{safe}.json"
            if cf.exists():
                try:
                    cached_data = json.loads(cf.read_text(encoding="utf-8"))
                    if cached_data.get("status") == "ok":
                        continue
                except Exception:
                    pass
            cards.append(c)
        cached = len(all_cards) - len(cards)

    print(f"共 {len(all_cards)} 张（缓存 {cached} 张，需抓取 {len(cards)} 张）")

    if not cards:
        print("所有卡片已缓存。")
    else:
        print(f"\n[Step 2] 异步并发抓取（{args.concurrency} 并发）...")
        results = asyncio.run(run(cards, args.concurrency, args.timeout))
        elapsed = time.time() - _start_time
        matched = sum(1 for r in results if r is not None)
        print(f"  完成! {elapsed:.0f}s | 匹配 {matched}/{len(cards)} 张")

    # Step 3: 合并
    print(f"\n[Step 3] 合并缓存 → {OUTPUT_FILE}")
    merged = {}
    not_found = []
    errors = 0

    for f in sorted(DATA_DIR.glob("*.json")):
        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            errors += 1
            continue
        if entry.get("status") == "ok" and entry.get("data"):
            merged[entry["data"]["file"].replace("ptcg/cards/", "").replace(".py", "")] = entry["data"]
        elif entry.get("status") == "not_found":
            not_found.append(f.stem.replace("_", " "))
        else:
            errors += 1

    elapsed = time.time() - _start_time
    output = {
        "metadata": {
            "source": "https://tcg.mik.moe/",
            "total": len(all_cards),
            "matched": len(merged),
            "not_found": len(not_found),
            "errors": errors,
            "elapsed_seconds": round(elapsed, 1),
            "concurrency": args.concurrency,
        },
        "cards": merged,
        "not_found": not_found,
    }
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"匹配: {len(merged)} | 未找到: {len(not_found)} | 错误: {errors} | {elapsed:.0f}s")

    if not_found:
        print(f"\n⚠ 未找到 ({len(not_found)}):")
        for name in sorted(not_found)[:10]:
            print(f"  - {name}")

    print("完成!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
