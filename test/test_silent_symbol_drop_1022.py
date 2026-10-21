"""조용히 사라지는 기호를 검사가 잡는가.

R17(점형 없는 기호) 집계가 기호를 **단독으로** 점역해 보고 판정하던 탓에 두 갈래를 놓쳤다.

1. 조합 표시(유니코드 분류 `Me`)를 아예 안 봤다 — 네모 문자 `⃞`(U+20DE). 「한국 점자 규정」
   제64항이 `_8 0l`로 묶으라고 정한 기호인데 점형이 없어 사라지고 그 사실조차 안 잡혔다.
2. 단독으로는 점형이 나오는데 문중에서는 사라지는 기호가 있다 — 채운 삼각형 `▲`(U+25B2).
   줄머리 규칙(`_LINE_BULLET_RE`)이 단독 판정에만 걸려 "안 사라진다"로 읽혔다.

2027 dev·val 1,746쪽 실측으로 194쪽(11.1%)이 이 둘에 걸린다(⃞ 336회 · ▲ 49회).
네모 빈칸이 사라지면 점역사가 채워 넣을 자리 자체를 잃는다.
"""
import pytest

from semojum_braille.encoder.translator import (
    dropped_symbols,
    translate_tagged_text,
)


def _vanishes(ch: str) -> bool:
    """글 사이에 넣었을 때 흔적 없이 사라지는가."""
    return translate_tagged_text("가" + ch + "나") == translate_tagged_text("가나")


@pytest.mark.parametrize("ch", ["⃞", "▲", "★", "†", "☐"])
def test_사라지는_기호는_집계에_잡힌다(ch):
    assert _vanishes(ch), f"{ch!r} 가 더는 사라지지 않는다 — 이 시험의 전제를 다시 보라"
    assert dropped_symbols("가" + ch + "나")[ch] == 1


@pytest.mark.parametrize("ch", ["□", "○", "△", "■", "●", "◦"])
def test_점형이_나오는_기호는_집계에_안_잡힌다(ch):
    assert not _vanishes(ch), f"{ch!r} 가 사라진다 — 무성 삭제다"
    assert ch not in dropped_symbols("가" + ch + "나")


def test_조합_표시도_센다():
    """`Me` 분류를 빠뜨리면 네모 문자가 통째로 빠진다."""
    assert dropped_symbols("답은 ⃞ 이다")["⃞"] == 1


def test_줄머리_점형이_문중_판정을_가리지_않는다():
    """▲ 는 줄머리에서는 점형이 나오지만 문중에서는 사라진다. 둘을 갈라 본다."""
    assert translate_tagged_text("▲ 배합공정").startswith("⠸⠲")
    assert dropped_symbols("공정은 ▲ 배합공정")["▲"] == 1
