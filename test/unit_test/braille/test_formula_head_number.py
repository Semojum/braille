"""해설 머리 굵은 문항 번호(`\\mathbf{2} \\quad (a+b)…`) 뒤는 한 칸이다.

gold 수학 Ⅰ(dev 009 답 3쪽) `#b 8a5b0` 는 `\\textbf{3} …` 머리와 같은 꼴이다. 예문은 지어낸 것이다.
"""
from __future__ import annotations

import semojum_braille.encoder.translator  # noqa: F401  (convert_latex 마지막 그물이 import 로 켜진다)
from semojum_braille.encoder.kor_math_rules import convert_latex


def test_굵은_머리_번호_뒤_괄호를_띄운다():
    assert convert_latex(r"\mathbf{3} \quad (x+1)^{2}").startswith("⠼⠉⠀⠦")
    assert convert_latex(r"\begin{array}{l} \mathbf{12} \quad (a-b) = 1 \end{array}").startswith("⠼⠁⠃⠀⠦")


def test_머리가_아니거나_수가_아니면_그대로():
    assert "⠀" not in convert_latex(r"x = \mathbf{2} \quad (a+b)")
    assert "⠀" not in convert_latex(r"\mathbf{v} \quad (a+b)")
