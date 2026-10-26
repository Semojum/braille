"""국어 문장 속 그리스 문자 이름 · 낱자 나열(#1592) — 「수학 점자」 제13항 [붙임] · 제12항 3호 · 「한글 점자」 제31항.

기대값은 규정 예문 점자다(정본 3479행 묶음 `0.a1`.b4n` · 3302~3304행 `0A1`;b4n` · `0,a1`;,b1`;,c4`).
"""
import pytest

from semojum_braille.encoder.translator import translate_with_breaks
from braille_ascii import ascii_to_unicode


def _tr(s: str) -> str:
    return "".join(translate_with_breaks(s)[0])


@pytest.mark.parametrize("text,brf", [
    (r"복소수 $\alpha, \beta$에 대하여", "~x,u,m`0.a1`.b4n`irj<:"),     # 제13항 [붙임] 예문(수식 태그로 온 꼴)
    ("복소수 α, β에 대하여", "~x,u,m`0.a1`.b4n`irj<:"),                 # 태그 없이 온 꼴
    ("다음 $a, b$에 대하여", "i<{5`0a1`;b4n`irj<:"),                      # 제12항 3호 예문
    ("세 점 $A, B, C$가 있다.", ",n`.s5`0,a1`;,b1`;,c4$`o/i4"),          # 제12항 3호 예문
    (r"각 $\theta$의 크기", "$a`0.?4w`f{@o"),                              # 홑 그리스 = 태그 없는 `각 θ의` 와 같다
])
def test_국어_문장_속_이름은_로마자_구간이다(text, brf):
    assert _tr(text) == ascii_to_unicode(brf, backtick="space")


@pytest.mark.parametrize("text", [r"$\sin\theta$의 값", r"$f(a, b)$의 값", r"함수 $y=\sin\theta$의 값", r"$\theta$"])
def test_식은_수식_꼴_그대로다(text):
    """함수 표기 · 식 안 나열 · 한글 없는 줄은 수식 경로다(제12항 1 · 2호)."""
    out = _tr(text)
    assert "⠴⠨" not in out and "⠲" not in out.replace("⠲⠺", "")
