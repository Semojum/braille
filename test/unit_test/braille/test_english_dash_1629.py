"""영어 글의 줄표(#1629) — 붙여 쓴 줄표가 이온 마이너스가 되지 않고, 한글 없는 영어 줄은 통일영어점자 줄표 ⠠⠤ 로 적는다.

규정: `braille-source/text/통일영어점자 규정_UEB2013.txt` 2.6.1 예 `I like x–it works.` = ,i l ;x,-x "ws4 · 과학 점자
제2항(이온은 위 첨자 기호 뒤 - 는 ⠔). 문장은 지어낸 것이고 기대 점자는 조문에서 손으로 옮겼다.
"""
import pytest

from semojum_braille.encoder.translator import translate_with_breaks


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0]).strip("⠀")


@pytest.mark.parametrize("text, cells", [
    # 붙여 쓴 줄표 · 띄어 쓴 줄표 모두 ⠠⠤, 줄표 뒤 낱말은 홀로 선다(very = ⠧)
    ("It was big—very big.", "⠠⠭⠀⠴⠀⠃⠊⠛⠠⠤⠧⠀⠃⠊⠛⠲"),
    ("a cat — a dog", "⠁⠀⠉⠁⠞⠀⠠⠤⠀⠁⠀⠙⠕⠛"),
])
def test_영어_줄_줄표는_통일영어점자_줄표(text, cells):
    assert _tr(text) == cells


def test_숫자_사이_줄표는_그대로():
    assert "⠠⠤" not in _tr("pages 10–12 here")


@pytest.mark.parametrize("text", ["HCO₃— 이온", "Rh—형 혈액"])
def test_원소_기호_뒤_줄표는_이온_마이너스(text):
    assert "⠘⠔" in _tr(text)


def test_한글_줄_줄표는_한글_꼴():
    assert _tr("가—나") == "⠫⠤⠤⠉"
