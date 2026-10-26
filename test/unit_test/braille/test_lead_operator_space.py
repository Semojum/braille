"""식 머리 연산 · 비교 기호도 뒤를 붙인다(「수학 점자」 제45항 · 제4항 연산 기호 붙임).

이어 쓴 유도 줄(`= \\log_{3}2 …`)이 수식 요소 하나로 들어오면 머리 기호 왼쪽에 글자가 없어 붙임 규칙이 안 걸렸다.
gold 수학 Ⅰ(dev 009) 식 머리 기호 뒤 붙임 95 · 빈칸 0. 기대 점형은 규정 표에서 손으로 옮겼다(지어낸 예문).
"""
from __future__ import annotations

import semojum_braille.encoder.translator  # noqa: F401  (convert_latex 마지막 그물이 import 로 켜진다)
from semojum_braille.encoder.kor_math_rules import convert_latex
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf, backtick="space")


def test_식_머리_등호():
    assert convert_latex(r"= 2 x + 1") == _b("33#bx5#a")


def test_식_머리_부등호():
    assert convert_latex(r"< x < 3") == _b("99x99#c")


def test_배열_첫_행_머리_등호():
    assert convert_latex(r"\begin{array}{l} = 2 x + 1 \end{array}") == _b("33#bx5#a")


def test_오른쪽이_한글이면_그대로():
    assert convert_latex(r"= \text{가}").startswith(_b("33`"))
