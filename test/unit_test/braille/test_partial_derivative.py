"""편도함수(「수학 점자」 제54항): ∂ 는 뒤 글자에 붙고, ∂ + 글자 하나는 안 묶고 거듭제곱 · 곱은 묶는다."""
import pytest

import semojum_braille.encoder.translator  # noqa: F401  (한글 훅 등록 — import 부작용)
from semojum_braille.encoder.kor_math_rules import convert_latex


@pytest.mark.parametrize("latex, expected", [
    (r"\frac{\partial z}{\partial x}=f_{x}(x,y)", "⠫⠭⠌⠫⠵⠒⠒⠋⠰⠭⠦⠭⠐⠀⠽⠴"),       # 1호(재추출 4000~4003행) $x/$z33f;x8x"`y0
    (r"\frac{\partial^2 z}{\partial x \partial y}=f_{xy}(x,y)",
     "⠷⠫⠭⠫⠽⠾⠌⠷⠫⠘⠼⠃⠵⠾⠒⠒⠋⠰⠷⠭⠽⠾⠦⠭⠐⠀⠽⠴"),                                    # 2호(4008~4011행) ($x$y)/($^#Bz)33f;(xy)8x"`y0
])
def test_규정_예문(latex, expected):
    assert convert_latex(latex) == expected


def test_미분소_d_는_그대로():
    # 제53항 2호 `d²y/dx²` = d^#by/dx^#b 는 안 묶는다 — ∂ 규칙이 d 에 번지지 않는다.
    assert convert_latex(r"\frac{d^2y}{dx^2}") == "⠙⠭⠘⠼⠃⠌⠙⠘⠼⠃⠽"
