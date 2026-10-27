"""쉼표 뒤 부호는 쉼표 뒤 한 칸을 둔다(「수학 점자」 제12항 [붙임 1] 쉼표 뒤 한 칸 예, 재추출 3329행 `a;#a"`a;#b"`…`).

부호는 다음 항의 머리라 뺄셈표처럼 앞을 붙이지 않는다. gold dev · val `⠐⠀⠔` 34 · `⠐⠔` 0. 예문은 지어낸 것이다.
"""
from __future__ import annotations

import semojum_braille.encoder.translator  # noqa: F401  (convert_latex 마지막 그물이 import 로 켜진다)
from semojum_braille.encoder.kor_math_rules import convert_latex
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf, backtick="space")


def test_좌표의_음수():
    assert convert_latex(r"(1, -2)") == _b('8#a"`9#b0')
    assert convert_latex(r"(1,-2)") == _b('8#a"`9#b0')


def test_뺄셈은_그대로_붙인다():
    assert convert_latex(r"a, b - c") == _b('a"`b9c')


def test_별표는_가르지_않는다():
    # 별표 `*` 는 빈칸 없는 ⠐⠔ 다. 쉼표(⠐ + 빈칸)와 헷갈려 가르면 안 된다
    assert "⠐⠔" in convert_latex(r"X^{A*}Y") and "⠐⠀⠔" not in convert_latex(r"X^{A*}Y")
