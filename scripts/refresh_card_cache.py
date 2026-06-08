#!/usr/bin/env python3
"""
DEPRECATED (2026-06-08): 已被 scripts/fetch_chinese_card_data.py + download_card_images.py 替代。
                      全部卡牌数据从 tcg.mik.moe API 获取，不再使用 tcgdex。
                      重建数据请运行:
                        uv run python scripts/fetch_chinese_card_data.py
                        uv run python scripts/download_card_images.py

原用途: Build card_data_cache.json from tcgdex API.
"""
    module = cls.__module__
    # e.g. "ptcg.cards.PAF.charizard_ex" -> "PAF/charizard_ex.py"
    parts = module.split(".")
    if len(parts) >= 3:
        return "/".join(parts[2:]) + ".py"
    return cls.__module__.replace(".", "/") + ".py"


if __name__ == "__main__":
    main()
