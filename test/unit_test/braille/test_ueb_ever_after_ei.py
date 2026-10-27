"""ever 머리글자 약자는 앞 글자가 e · i 면 쓰지 않는다 — 통일영어점자 10.7.4(`통일영어점자 규정_UEB2013.txt` 5194~5195행).

낱말은 조문 예에 없는 것으로 골랐고 기대 점자는 조문대로 손으로 옮겼다(ch = ⠡ · er = ⠻ · ever = ⠐⠑).
"""
import pytest

from semojum_braille.encoder import eng_braille


@pytest.mark.parametrize("word, cells", [
    ("achiever", "⠁⠡⠊⠑⠧⠻"),     # 앞이 i — ever 안 씀, er 묶음표
    ("reliever", "⠗⠑⠇⠊⠑⠧⠻"),
    ("fever", "⠋⠐⠑"),            # 앞이 f — ever 씀
    ("clever", "⠉⠇⠐⠑"),
])
def test_ever_앞_글자(word, cells):
    assert eng_braille.translate(word) == cells
