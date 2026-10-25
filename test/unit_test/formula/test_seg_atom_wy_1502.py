"""#1502 — 벡터 · 선분 기호 바로 뒤 글자가 w · y 여도 분수 칸 묶음 판정에서 인수 하나로 센다(#1445 와 같게).

수학 점자 제7항 3호(재추출 3149행): 분자 · 분모가 곱이면 묶는다. `2\\vec{v}` 와 `2\\vec{w}` 는 같은 꼴이다.
기대 점자는 손으로 옮겼다: 분모 3 ⠼⠉ · 분수표 ⠌ · 묶음 ⠷…⠾ · 2 ⠼⠃ · 벡터 ⠒⠕ · w ⠺ · y ⠽ · v ⠧.
"""
import pytest

from semojum_braille.encoder import translator  # noqa: F401 — convert_latex 는 translator import 뒤에 잰다(_w2c 훅)
from semojum_braille.encoder.kor_math_rules import convert_latex


@pytest.mark.parametrize("latex,want", [
    (r"\frac{2\vec{v}}{3}", "⠼⠉⠌⠷⠼⠃⠒⠕⠧⠾"),     # 종전에도 맞던 꼴
    (r"\frac{2\vec{w}}{3}", "⠼⠉⠌⠷⠼⠃⠒⠕⠺⠾"),
    (r"\frac{2\vec{y}}{3}", "⠼⠉⠌⠷⠼⠃⠒⠕⠽⠾"),
])
def test_벡터_뒤_w_y도_인수_하나(latex, want):
    assert convert_latex(latex) == want
