"""수식 속 홑 로마자가 한글 글에 붙으면 로마자표 꼴로 적는다(원장 C-155, 「한글 점자」 제32항).

글 경로는 이미 이 꼴이다. 수식 요소(`\\text{…}` 가 섞인 LaTeX)에는 그 꼴이 없어 `⠝⠀⠕` 처럼 나갔다.
기대 점형은 규정 예문(재추출 1654행)이거나 지어낸 예문에 그 꼴을 손으로 적용한 것이다.
"""
from __future__ import annotations

import semojum_braille.encoder.translator  # noqa: F401  (convert_latex 마지막 그물이 import 로 켜진다)
from semojum_braille.encoder.kor_math_rules import convert_latex
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf, backtick="space")


def test_규정_예문_나열():
    # 재추출 1654행 `다음 a, b, c의 값으로 …` = `i<{5`0a1`;b1`;c4w`$b'{"u…`
    assert convert_latex(r"\text{다음 } a, b, c \text{의 값으로}") == _b("i<{5`0a1`;b1`;c4w`$b'{\"u")


def test_괄호_속_조건():
    assert _b("80n4o") in convert_latex(r"a_{n} = 1 (n\text{이 홀수})")


def test_곱의_글자는_그대로():
    # `2 k` 의 k 는 곱이다. 앞이 식 머리 · 여는 괄호 · 쉼표 · 다른 글이 아니면 안 합친다
    assert "⠴⠅" not in convert_latex(r"2 k \text{의 값}")
