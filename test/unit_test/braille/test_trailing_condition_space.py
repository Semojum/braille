"""식 끝 조건 괄호 앞은 한 칸이다(연립식 행 #1594 와 같은 판정을 일반 식에).

gold 수학 Ⅰ(dev 009) 수식 요소 식 끝 조건 괄호 앞 한 칸 16 · 붙음 0. 함수 인수(`\\log_{2}(x-2)` · `P(X=1)`)는 그대로다.
예문은 지어낸 것이고 기대 점형은 규정 표에서 손으로 옮겼다.
"""
from __future__ import annotations

import semojum_braille.encoder.translator  # noqa: F401  (convert_latex 마지막 그물이 import 로 켜진다)
from semojum_braille.encoder.kor_math_rules import convert_latex
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf, backtick="space")


def test_식_끝_조건():
    assert convert_latex(r"y = 2^{x} (x > 0)") == _b("y33#b~x`8x55#j0")


def test_대문자_함수_인수는_그대로():
    assert convert_latex(r"P(X=1)") == _b(",p8,x33#a0")


def test_관계_기호_없는_인수는_그대로():
    assert "⠀" not in convert_latex(r"y=\log_{2}(x-2)")


def test_로마자가_든_한글_조건도_띄운다():
    """gold 수학 Ⅰ 의 `r (p, q, r은 상수)` · `#b (l은 자연수)` 꼴. 합친 홑 로마자(C-155)도 로마자로 센다."""
    head = convert_latex(r"y = ax + b")
    assert convert_latex(r"y = ax + b (a, b \text{는 상수})").startswith(head + "⠀⠦")
    assert convert_latex(r"y = 2x (\text{단,} x \text{는 자연수})").startswith(convert_latex(r"y = 2x") + "⠀⠦")


def test_한글만_든_묶음과_기호_없는_앞은_붙인다():
    """한글만 든 묶음은 이름표 · 단위(`(가)` · `(라디안)`)이고, 기호 없는 앞은 표 칸 이름표(`㉢(S기)`)다."""
    for latex in (r"x = 3 (\text{가})", r"1^{\circ} = \frac{\pi}{180} (\text{라디안})", r"㉢(S\text{기})",
                  r"l = 3 (\text{cm})"):
        assert "⠀⠦" not in convert_latex(latex), latex
