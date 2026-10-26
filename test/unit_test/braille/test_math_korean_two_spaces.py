"""수식 요소 속 한글 앞뒤는 두 칸이다(「수학 점자」 제11항, 재추출 3235행).

종전엔 입력 띄움을 따라 0 · 1 · 2칸이 섞였다. 그대로 두는 자리(연산 기호 곁 · 원문자 뒤 · 단순 수 · 묶음 안)도 같이 지킨다.
★ 기대 점형은 규정 원문 BRF 를 옮기거나(행 번호를 단다) 규칙에서 손으로 적었다. 예문은 지어낸 것이다.
"""
from __future__ import annotations

import pytest

import semojum_braille.encoder.translator  # noqa: F401  (convert_latex 마지막 그물이 import 로 켜진다)
from semojum_braille.encoder.kor_math_rules import convert_latex
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf, backtick="space")


def test_규정_예문():
    # 재추출 3241행 `tanx의 값은 (3+√5)/2이다.`
    assert convert_latex(r"\tan x \text{의 값은} \frac{3+\sqrt{5}}{2} \text{이다.}") == _b("6tx``w`$b'z``#b/(#c5>#e)``oi4")


@pytest.mark.parametrize("latex", [
    r"x<a \text{또는} x>b", r"x<a\text{또는}x>b", r"x<a \text { 또는 } x>b", r"x<a\ \text{또는}\quad x>b"])
def test_입력_띄움과_무관하게_두_칸(latex):
    assert convert_latex(latex) == _b("x99a``,iucz``x55b")


def test_연산_기호_곁은_한_칸():
    # 「한글 점자」 제46항 예 `나루 + 배 = 나룻배`(재추출 2064행)
    assert convert_latex(r"\text{나루} + \text{배} = \text{나룻배}") == _b("c\"m`5`^r`33`c\"m'^r")


def test_단순_수는_한_칸():
    # 제11항은 단순 수를 두 칸 대상에서 뺀다
    assert convert_latex(r"y=2 \text{일 때} 3, 4") == _b("y33#b``o1`,ir`#c\"`#d")


def test_원문자_뒤는_붙인다():
    got = convert_latex(r"㉣ \text{에서} y=1")
    assert got.endswith(_b("n,s``y33#a")) and _b("`n,s") not in got


def test_묶음_안_한글은_그대로():
    assert "⠀⠀" not in convert_latex(r"\frac{\text{가로}}{\text{세로}}")


def test_식_머리_부호는_붙인다():
    assert convert_latex(r"\text{따라서} - 2 < x") == _b(",i\"<,s``9#b99x")
