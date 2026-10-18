"""수식 변환 갈래 묶음(#1443 · 네모 친 답 · 그리스 글자 밑 첨자 · 빗금 둘 평행 · lim 점근값 뒤 빈칸 · 기울인 Δ · 수 뒤 칸).

기대값은 「한국 점자 규정」 원문 예문(braille-source/text/한국 점자 규정_재추출.txt 행 번호)의 BRF 를 그대로 점자로
바꾼 것이다(백틱은 규정 관례대로 빈칸). 예문이 없는 꼴은 2027 수학Ⅰ gold(dev EBS-E26-009) 실물 점형을 쪽과 함께
적는다(gold BRF 의 백틱 ⠈ 는 `@` 로 적는다). 입력은 MinerU · formula_opt 정규화 뒤 실물 꼴이다.
"""
import pytest

import semojum_braille.encoder.translator  # noqa: F401 — \text 한글 훅이 이 import 로 걸린다
from semojum_braille.encoder.kor_math_rules import convert_latex
from semojum_braille.encoder.text_braille import translate_body
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"\boxed {\text {(가)}}", "_88'$,00l"),                     # 제73항 [붙임](2946~2947 · 2952행) 네모 친 (가)
    (r"\boxed {\frac {1}{2}}", "_8#b/#a0l"),                     # 해설 50쪽 — 분수를 통째로 묶는다
    (r"\left(\boxed {m + 2}\right) a _ {m + 1}", "8_8m5#b0l0a;(m5#a)"),   # 해설 51쪽 — 괄호 안 네모
    (r"\left(\frac {1}{m + 1}\right) + \boxed {\text {(가)}} \\ = 1", "8(m5#a)/#a05_88'$,00l33#a"),  # 본문 94쪽 + · = 붙임
])
def test_네모_친_답은_네모로_묶는다(latex, brf):
    assert convert_latex(latex) == _b(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"α^ {2} + β^ {2}", ".a^#b5.b^#b"),            # 제18항 1호(3528행) 지수는 ^ 뒤 — gold 해설 52쪽 α²
    (r"3 β^ {2} - 4", "#c.b^#b9#d"),                # gold 해설 45쪽
    (r"γ^ {y - x}", ".g^(y9x)"),                    # 제18항 [붙임](3540행) 다항식 지수는 묶는다 — 해설 47쪽
    (r"α_ {1} = - 2 d", ".a;#a339#b\"d"),           # 제19항 1호(3566행) 아래첨자는 ; 뒤 — 수학 II 해설 44쪽
    (r"α^ {\circ}", ".a0d"),                        # 각도는 그대로(도 ⠴⠙)
])
def test_그리스_글자_밑의_첨자(latex, brf):
    """수식 요소는 formula_opt 가 `\\alpha` 를 `α` 로 펴서 들어온다. 종전에는 ^ 가 캐럿 ⠈⠢, _ 가 밑줄 ⠸⠤ 로 샜다."""
    assert convert_latex(latex) == _b(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"AB / / CD", ",,AB;2,,CD"),                                                    # 제44항(3783~3785행)
    (r"\overline {\mathrm{BC}} / / \overline {\mathrm{MN}}", "@c,,bc;2@c,,mn"),      # 해설 37쪽
    (r"\overline{AD} // \overline{BC}", "@c,,ad;2@c,,bc"),                            # 본문 55 · 63쪽(글 속 수식)
])
def test_빗금_둘은_평행(latex, brf):
    assert convert_latex(latex) == _b(brf)


def test_빗금_하나와_URL_은_그대로():
    assert convert_latex(r"a / b") == _b("a _/ b")
    assert "⠰⠆" not in "".join(translate_body("링크 https://q7rx.kr/V1im 에서")[0])


@pytest.mark.parametrize("latex,brf", [
    (r"\lim_ {x \longrightarrow \infty} f (x)", "LIM;X 3o = F8X0"),       # 제51항(3908~3910 · 3918행)
    (r"\operatorname* { l i m } _ { x \longrightarrow b } { g ( x ) }", "LIM;X 3o B G8X0"),   # 3914행 · 글 속 수식 꼴
])
def test_lim_점근값_뒤_빈칸(latex, brf):
    assert convert_latex(latex) == _b(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"\lim_{x \to \pm \infty} (1 + \frac{1}{x})^{x} = e", "lim;X 3o 59= 8#A5X/#A0^X33E"),   # 제51항(3928행)
    (r"\lim_{a \to 0} \frac{\log(a+1)}{a}", "LIM;A 3o #J A/_8A5#A0"),                        # 제51항(3923행)
    (r"\lim_ {x \longrightarrow - 2} f (x)", "LIM;X 3o 9#B F8X0"),          # 2027 gold `LIM;X 3O 9#B` — 수학 II 본문 37쪽
    (r"\lim_ {x \to - \infty} f (x)", "LIM;X 3o 9= F8X0"),                 # 2027 gold `3O 9= F8X0` — 수학 II 본문 9쪽
    (r"\lim_ {x \to 0 -} f (x)", "LIM;X 3o #J9 F8X0"),                     # 2027 gold `3O #J9 F8X0` — 한쪽 극한
    (r"\lim_ {x \to 0 ^ {-}} f (x)", "LIM;X 3o #J9 F8X0"),                 # 올린 부호 — 수학 II 해설 12쪽
    (r"\lim_ {t \to k +} g (t)", "LIM;T 3o K5 G8T0"),                       # 2027 gold `3O A5 F8X0` 꼴 — 수학 II 해설 19쪽
    (r"\lim _ {t \to x _ {1} -} g (t)", "LIM;T 3o X;#A9 G8T0"),            # 범위 안 중괄호 — 수학 II 해설 19쪽
    (r"\lim_{t \to \frac{3}{4} -} g(t)", "LIM;T 3o #D/#C9 G8T0"),          # 분수 점근값 — 종전엔 첫 `}` 에서 끊겼다
])
def test_lim_점근값_부호와_화살표_칸(latex, brf):
    """제51항(3908~3910행) 화살표 양쪽 · 점근값 뒤 칸은 점근값의 부호와 상관없이 선다. 종전에는 11e 연산 붙임이
    뺄셈표 ⠔ 둘레 칸으로 보고 지웠다(`lim;x`3o9#b`)."""
    assert convert_latex(latex) == _b(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"\varDelta y", ",.dy"),                                        # 제52항(3936~3940행)
    (r"\frac{\varDelta y}{\varDelta x}", ",.dx/,.dy"),               # 제52항(3938행)
    (r"[ t , t + \varDelta t ]", "('t\" t5,.dt,)"),                  # 수학 II 본문 88쪽
])
def test_기울인_대문자_그리스(latex, brf):
    assert convert_latex(latex) == _b(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"2 \sqrt {6}", "#b>#f"),                          # 원장 M-14 · 제12항 1호 [다만](3317~3318행) — gold 해설 16쪽
    (r"\frac {2 \sqrt {6}}{5}", "#e/(#b>#f)"),          # gold 해설 16쪽 `#e/(#b>#f)`
    (r"\sin^ {2} θ + \cos^ {2} θ = 1", "6s^#b.?56c^#b.?33#a"),   # 지수 뒤 그리스 글자 — gold 60 : 0
])
def test_수_뒤_칸(latex, brf):
    assert convert_latex(latex) == _b(brf)
