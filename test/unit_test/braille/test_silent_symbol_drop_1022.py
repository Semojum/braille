"""조용히 사라지는 기호를 R17 셈이 잡는가(#1555, 엔진 Semojum/braille#96 을 정본으로 옮김).

R17(점형 없는 기호) 셈이 기호를 **홀로** 점역해 보고 판정하던 탓에 두 갈래를 놓쳤다.

1. 조합 표시(유니코드 분류 `Me`)를 아예 안 봤다. 네모 문자 `⃞`(U+20DE)가 여기 걸린다. 「한국 점자 규정」
   제64항이 네모 문자를 `_8 0l`로 묶어 나타내라고 정했는데(재추출 2566~2567행) 점형이 없어 사라지고
   그 사실조차 안 잡혔다.
2. 홀로는 점형이 나오는데 문중에서는 사라지는 기호가 있다. 채운 삼각형 `▲`(U+25B2)은 줄머리 규칙
   (`_LINE_BULLET_RE`)이 홀로 판정에만 걸려 "안 사라진다"로 읽혔다.

네모 빈칸이 사라지면 점역사가 채워 넣을 자리 자체를 잃는다. 예문은 지어낸 것이다.
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
    assert translate_tagged_text("▲ 첫째 항목").startswith("⠸⠲")
    assert dropped_symbols("다음은 ▲ 첫째 항목")["▲"] == 1


@pytest.mark.parametrize("text", [
    "▲ 첫째 항목",          # 줄머리 글머리표로 점형이 나온다
    "▲▲ 마을",             # 빈자리 표 묶음으로 점형이 나온다
    "다음은\n▲ 첫째 항목",   # 줄이 바뀌면 다시 줄머리다
])
def test_점형이_나오는_자리는_안_센다(text):
    """#1555. 글자 하나로만 판정하면 ▲ 를 늘 '사라진다' 로 세어 점형이 나오는 자리에도 R17 이 붙었다."""
    assert "▲" not in dropped_symbols(text)


def test_자리마다_센다():
    assert dropped_symbols("▲ 첫째, 둘째 ▲ 셋째")["▲"] == 1        # 줄머리 것은 점형, 문중 것만 사라진다
    assert dropped_symbols("정⃞답⃞")["⃞"] == 2


@pytest.mark.parametrize("text,ch", [
    ("에너지는 kcal/kg´h 이다", "´"),     # 사라지지만 gh 약자를 막는다
    ("가방에 I♥NY 라고 적혀 있다", "♥"),   # 사라지지만 대문자 묶음을 가른다
    ("g(x) ⟺ f(x)", "⟺"),
])
def test_사라지며_이웃에_흔적을_남겨도_센다(text, ch):
    """기호를 빼고 맞대면 이웃이 달라져 '안 사라졌다' 로 읽힌다. 그래서 늘 사라지는 기호로 바꿔 넣고 맞댄다."""
    assert dropped_symbols(text)[ch] == 1


def test_윗첨자처럼_점형이_나오는_자리는_안_센다():
    assert "⁶" not in dropped_symbols("둘의 곱은 2⁶ 이다")


def test_중립_기호는_늘_사라진다():
    """`translator._DROP_NEUTRAL` 의 전제다. 점형이 생기면 다른 글자로 바꾼다."""
    from semojum_braille.encoder.translator import _DROP_NEUTRAL
    assert not translate_tagged_text(_DROP_NEUTRAL).strip("⠀ ")
    assert translate_tagged_text("가" + _DROP_NEUTRAL + "나") == translate_tagged_text("가나")
    assert translate_tagged_text("▲" + _DROP_NEUTRAL) != translate_tagged_text("▲▲")    # 묶음 규칙에 안 걸린다
