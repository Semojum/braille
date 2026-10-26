"""연립식 행의 식과 조건 사이는 한 칸이다(수학 제6항).

규정 예문(재추출 3107행) `f8x0337'a8#a9x0`8#j66x66#a0` 은 `a(1−x)` 와 조건 `(0≤x≤1)` 사이를 한 칸 띄운다.
2027 gold(홀드아웃 뺀 전권 연립식 866개)의 조건 괄호도 한 칸 249 · 붙음 1 이다. 열 구분 `&` 로 적든 그냥 이어 적든 같다.
★ 예문은 지어낸 것이다(코퍼스 · gold 줄을 넣지 않는다). 기대 점형은 규정 제4·6항 표에서 손으로 옮겼다.
"""
from __future__ import annotations

import semojum_braille.encoder.translator  # noqa: F401  (convert_latex 마지막 그물이 import 로 켜진다)
from semojum_braille.encoder.kor_math_rules import convert_latex
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf, backtick="space")


def test_규정_예문_첫_행은_식과_조건_사이가_한_칸():
    got = convert_latex(r"f(x)=\begin{cases} a(1-x) & (0\le x\le 1) \\ b(x-1) & (1\le x\le 2) \end{cases}")
    assert got.startswith(_b("f8x0337'a8#a9x0`8#j66x66#a0"))


def test_열_구분_없이_적은_조건도_한_칸():
    got = convert_latex(r"g(t)=\left\{\begin{array}{l} 5 (t>2) \\ 0 (t\le 2) \end{array}\right.")
    assert got == _b("g8t0337'#e`8t55#b0``#j`8t66#b0,7")


def test_괄호_없는_조건이_수와_곱으로_붙지_않는다():
    got = convert_latex(r"h(x)=\begin{cases} 1 & x>0 \\ 0 & x\le 0 \end{cases}")
    assert got == _b("h8x0337'#a`x55#j``#j`x66#j,7")


def test_정렬용_앰퍼샌드는_기호에_붙인다():
    assert convert_latex(r"\left\{\begin{aligned} x+y &= 3 \\ x-y &= 1 \end{aligned}\right.") == \
        convert_latex(r"\left\{\begin{array}{l} x+y=3 \\ x-y=1 \end{array}\right.")


def test_조건만_있는_행은_앞_행에_한_칸으로_붙는다():
    assert convert_latex(r"\left\{\begin{array}{l} x^{2}+1 \\ \quad (x>0) \\ 2x \\ \quad (x\le 0) \end{array}\right.") == \
        convert_latex(r"\begin{cases} x^{2}+1 & (x>0) \\ 2x & (x\le 0) \end{cases}")


def test_행_머리_부호는_뒤에_붙인다():
    # 수학 제45항: 연산 · 부호 기호는 붙여 쓴다. 식 첫머리는 이미 붙는데 행 구분 뒤는 빈칸이 남았다
    got = convert_latex(r"k(x)=\begin{cases} 1 & (x>0) \\ - \sqrt {3} & (x<0) \end{cases}")
    assert got == _b("k8x0337'#a`8x55#j0``9>#c`8x99#j0,7")


def test_행_끝_함수_인수는_가르지_않는다():
    got = convert_latex(r"\left\{\begin{array}{l} y=\log_{2}(x-2) \\ y=f(x) \end{array}\right.")
    assert "⠀⠦" not in got
