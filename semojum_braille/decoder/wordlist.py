"""kiwi 없이 쓰는 한국어 낱말 판정. `[kiwi]` 선택 의존을 안 깔았을 때 역점역이 부른다.

낱말 목록(`kor_words.json`)은 한국어 교재 묵자 1,355쪽(2027 수능특강 비영어 12권)의 한글 덩어리
가운데 두 번 이상 나오고 두 음절 이상인 것이다. 영어 교재와 정답 점자는 쓰지 않았다.
만드는 법은 `tools/build_word_list.py`, kiwi 판정과 견준 측정은 `docs/decoder.md`.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

WORDS_PATH = Path(__file__).with_name("kor_words.json")


@lru_cache(maxsize=1)
def words() -> frozenset[str]:
    """낱말 목록. 처음 부를 때 한 번 읽는다. 없거나 깨지면 예외(빈 목록으로 조용히 돌지 않는다)."""
    return frozenset(json.loads(WORDS_PATH.read_text(encoding="utf-8"))["words"])


def known(runs: list[str]) -> bool:
    """한글 덩어리가 모두 두 음절 이상이고 목록에 있으면 True. 덩어리가 없으면 False."""
    ws = words()
    return bool(runs) and all(len(r) >= 2 and r in ws for r in runs)
