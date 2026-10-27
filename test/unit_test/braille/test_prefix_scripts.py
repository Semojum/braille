"""선행 첨자(왼쪽 첨자) — 규정 제18·19항 2호.

`_{8}\\mathrm{O}`(원자번호 8인 산소)처럼 **base 없이 첨자가 먼저** 오는 식에서,
base를 요구하는 일반 첨자 규칙이 못 잡아 남은 `_`가 symbol_table의 **밑줄 기호**로,
`^`는 **캐럿**으로 새 나갔다. 규정은 이 자리를 왼쪽 첨자로 규정한다 —
첨자 기호 + **묶음 괄호** + 본 문자.

여기서 지키는 것 셋:
  1. 선행 첨자가 첨자 기호(⠘/⠰) + 묶음으로 나온다.
  2. **base가 있는 일반 첨자는 건드리지 않는다** — 정적분 아래끝·합·극한·순열이 대상이다.
     추출물이 `\\int _{a}`처럼 공백을 끼워 내므로 "앞 문자가 공백이면 선행 첨자"로 보면
     이것들이 전부 끌려간다(실측으로 확인해 허용 목록 방식으로 바꿨다).
  3. 어떤 경우에도 점자 아닌 문자를 내보내지 않는다.

원소 기호 앞의 원자 번호 · 질량수(핵종)는 왼쪽 첨자가 아니다. 「과학 점자」 제3항(재추출 4348~4362행)은
원소 기호를 먼저 적고 원자 번호는 아래 첨자, 질량수는 위 첨자로 적는다(2026-10-27).
"""
from __future__ import annotations

import re

import pytest

import semojum_braille.encoder.translator  # noqa: F401  (한글 훅 등록 — import 부작용)
from semojum_braille.encoder.kor_math_rules import convert_latex
from semojum_braille.encoder.translator import translate_with_breaks

_NON_BRAILLE = re.compile(r"[^⠀-⣿\n ]")
_SUP = "⠘"   # 위첨자 기호
_SUB = "⠰"   # 아래첨자 기호


@pytest.mark.parametrize(
    "latex, mark",
    [
        (r"_{2}x", _SUB),
        (r"^{n}a", _SUP),
        (r"{}^{t}B", _SUP),                   # 전치 — 질량수는 숫자뿐이라 붕소로 읽지 않는다
        (r"_{8}O_{2}", _SUB),                 # 원소 뒤 아래첨자가 이어지면 핵종으로 옮기지 않는다
        (r"_{2}O", _SUB),                     # 원자 번호가 원소와 다르면(O = 8) 쪼개진 화학식 조각(`H₂O` 의 `₂O`)이다
        (r"^{2}O", _SUP),                     # 질량수가 원자 번호보다 작으면 핵종이 아니다
    ],
)
def test_선행_첨자는_첨자_기호로_시작한다(latex, mark):
    got = convert_latex(latex)
    assert got.startswith(mark), f"{latex!r} → {got!r}"


@pytest.mark.parametrize(
    "latex, expected",
    [
        (r"^{235}_{92}\mathrm{U}", "⠠⠥⠰⠼⠊⠃⠘⠼⠃⠉⠑"),        # 과학 제3항 `²³⁵₉₂U` = ,u;#ib~#bce (재추출 4353행)
        (r"_{8}\mathrm{O}", "⠠⠕⠰⠼⠓"),                     # `₈O` = ,o;#h (4355행)
        (r"^{7}\mathrm{Li}", "⠠⠇⠊⠘⠼⠛"),                   # `⁷Li` = ,li~#g (4357행)
        (r"_{a}\mathrm{Zn}^{m}", "⠠⠵⠝⠰⠁⠘⠍"),              # `ₐZnᵐ` = ,zn;a~m (4359행)
        (r"^{9}_{4}\mathrm{Be}^{2+}", "⠠⠃⠑⠰⠼⠙⠘⠼⠊⠘⠼⠃⠢"),  # `⁹₄Be²⁺` = ,be;#d^#i^#b5 (4362행)
        (r"{}_{6}^{14}C", "⠠⠉⠰⠼⠋⠘⠼⠁⠙"),                  # 아래첨자가 먼저 온 꼴 · `{}` 표지
    ],
)
def test_핵종은_원소_기호를_먼저_적는다(latex, expected):
    assert convert_latex(latex) == expected


def test_유니코드_핵종도_같다():
    """글 경로(`inline_math`)로 온 `ₐZnᵐ` 의 ᵐ 이 첨자 표에 없어 수식 구간 밖으로 떨어졌다."""
    assert "".join(translate_with_breaks("ₐZnᵐ")[0]).strip("⠀") == "⠠⠵⠝⠰⠁⠘⠍"


@pytest.mark.parametrize(
    "latex",
    [
        r"_{8}\mathrm{O}",
        r"^{7}\mathrm{Li}",
        r"^{235}_{92}\mathrm{U}",
        r"{}^{t}A",
        r"\int_{a}^{b} f(x) dx",
        r"\int _{a} ^{b} f(x) dx",
        r"\sum_{k=1}^{n} k",
        r"\lim_{h \to 0} f(x)",
        r"_{n}P_{r}",
        r"\mathrm{H}_{2}\mathrm{O}",
        r"\mathrm{HCO}_{3}^{-}",
        r"x_{2}",
        r"x^{2}",
        r"S _ {2}",
    ],
)
def test_점자_아닌_문자를_내보내지_않는다(latex):
    """밑줄 기호·캐럿으로 새던 자리가 막혔는지. 원래 결함이 여기서 보였다."""
    got = convert_latex(latex)
    assert not _NON_BRAILLE.findall(got), f"{latex!r} → {got!r}"


class TestBase가_있으면_건드리지_않는다:
    """추출물의 공백(`\\int _{a}`)에 속아 일반 첨자를 선행 첨자로 잡으면 안 된다."""

    @pytest.mark.parametrize("latex", [
        r"\int_{a}^{b} f(x) dx",
        r"\int _{a} ^{b} f(x) dx",     # 공백 낀 꼴 — MinerU가 이렇게 낸다
    ])
    def test_정적분_아래끝은_묶음으로_감싸지_않는다(self, latex):
        """제57항 정적분은 `∫ ⠰아래끝 위끝 본식` 꼴이다 — 묶음이 끼면 형식이 깨진다."""
        got = convert_latex(latex)
        assert f"{_SUB}⠦" not in got, f"아래끝이 묶음으로 감싸졌다: {got!r}"

    def test_공백_유무가_결과를_바꾸지_않는다(self):
        assert convert_latex(r"\int_{a}^{b} f(x) dx") == convert_latex(r"\int _{a} ^{b} f(x) dx")

    @pytest.mark.parametrize("latex, other", [
        (r"x_{2}", r"x _ {2}"),
        (r"S_{1}", r"S _ {1}"),
    ])
    def test_일반_아래첨자도_공백_무관(self, latex, other):
        assert convert_latex(latex) == convert_latex(other)

    def test_순열은_그대로다(self):
        """`_{n}P_{r}`은 제58항 순열 — 선행 첨자로 분해되면 안 된다."""
        got = convert_latex(r"_{n}P_{r}")
        assert got.startswith("⠠"), f"순열 머리가 깨졌다: {got!r}"


@pytest.mark.parametrize(
    "latex, expected",
    [
        (r"2\,{}_{7}P_{2}", "⠼⠃⠠⠏⠷⠼⠛⠀⠼⠃⠾"),              # 제62항 2호 예(재추출 4229~4230행) `2 ₇P₂` = #B,P(#G`#B)
        (r"2\,{}_{n-1}C_{r-1}", "⠼⠃⠠⠉⠷⠝⠔⠼⠁⠀⠗⠔⠼⠁⠾"),     # 3호 예(4241~4242행) `2 ₙ₋₁Cᵣ₋₁` = #B,C(N9#A`R9#A)
        (r"2{}_{7}P_{2}", "⠼⠃⠠⠏⠷⠼⠛⠀⠼⠃⠾"),                # 띄움 없이 붙어 와도 순열이다
    ],
)
def test_계수가_붙은_순열은_계수와_기호를_붙인다(latex, expected):
    assert convert_latex(latex) == expected
