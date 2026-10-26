"""기호 사이 줄임표 곁은 한 칸이다(원장 C-189, 관행).

규정 예문에 기호 사이 줄임표가 없다(수학 편 예문은 쉼표 뒤 `a₁,a₂,a₃,...` · 순환소수 `0.1999⋯` 뿐). 2027 gold(홀드아웃 뺌)
`+ ⋯ +` 꼴 앞뒤 띄움 169 · 붙음 9(한 권). 기대 점형은 지어낸 예문에 규칙을 손으로 적용해 적었다.
"""
from __future__ import annotations

import semojum_braille.encoder.translator  # noqa: F401  (convert_latex 마지막 그물이 import 로 켜진다)
from semojum_braille.encoder.kor_math_rules import convert_latex
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf, backtick="space")


def test_덧셈_사이_줄임표():
    assert convert_latex(r"a_1 + a_2 + \cdots + a_n") == _b("a;#a5a;#b5`,,,`5a;n")


def test_붙여_적은_입력도_같다():
    assert convert_latex(r"1+2+\dots+n") == _b("#a5#b5`,,,`5n")


def test_쉼표_뒤_줄임표는_그대로():
    # 수학 제12항 [붙임 1] 예(재추출 3329행) `a;#a"`a;#b"`a;#c"`,,,`
    assert convert_latex(r"a_1, a_2, a_3, \cdots") == _b('a;#a"`a;#b"`a;#c"`,,,')


def test_순환소수_줄임표는_붙인다():
    # 수학 제11항 예(재추출 3243행) `#j4aiii,,,`
    assert convert_latex(r"0.1999\cdots") == _b("#j4aiii,,,")
