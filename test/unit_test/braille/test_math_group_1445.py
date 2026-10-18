"""수식 묶음 괄호 다섯 꼴(#1445 · 로그 진수 · 분수 칸).

기대값은 「한국 점자 규정」 원문 예문(braille-source/text/한국 점자 규정_재추출.txt 행 번호)의 BRF 를 그대로 점자로
바꾼 것이다(백틱은 규정 관례대로 빈칸). 예문이 없는 꼴은 2027 수학Ⅰ gold(dev EBS-E26-009) 실물 점형을 쪽과 함께
적는다(gold BRF 의 백틱 ⠈ 는 `@` 로 적는다). 입력은 MinerU 실물 꼴이다(formula_opt 정규화를 거쳐도 같은 출력).
"""
import pytest

import semojum_braille.encoder.translator  # noqa: F401 — \text 한글 훅이 이 import 로 걸린다
from semojum_braille.encoder.kor_math_rules import convert_latex
from braille_ascii import ascii_to_unicode


def _b(brf: str) -> str:
    return ascii_to_unicode(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"\log_ {8} \left(\frac {1}{2}\right) ^ {x}", "_,8(8#b/#a0~x)"),       # 해설 5쪽 — 지수까지 진수
    (r"\log_ {3} (x - n) ^ {2}", "_,3(8x9n0~#b)"),                         # 해설 14쪽
    (r"\log_ {4} (x - 1) (x + 2) = 1", "_,4(8x9#a08x5#b0)33#a"),           # 해설 10쪽 — 두 인수 통째
    (r"\log_ {2} (x + 1)", "_,2(8x5#a0)"),                                 # 제46항 [붙임 2] 예(3836행)
    (r"\log_ {e} (2 + h)", "_;e8#b5h0"),                                   # 제46항 [다만] 예(3841행) — 밑이 문자면 안 묶음
])
def test_로그_괄호_진수는_뒤_지수와_인수까지_묶는다(latex, brf):
    assert convert_latex(latex) == _b(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"\log_ {a} \frac {u}{v}", "_;a(v/u)"),                               # 제46항 [붙임 2] 예(3834행 `_;A(V/U)`)
    (r"\log_ {2} \frac {1}{2 ^ {\frac {3}{4}}}", "_,2(#b~(#d/#c)/#a)"),    # 해설 4쪽 — 분모 지수가 분수
    (r"\log_ {p} \frac {1}{2} a", "_;p(#b/#a\"a)"),                        # 해설 13쪽 — 분수 뒤 곱
    (r"\log \frac {2 ^ {7}}{1 0 ^ {2}}", "_(#aj~#b/#b~#g)"),              # 해설 13쪽 — 밑 없는 log
    (r"\log_ {3} \frac {a _ {5}}{a _ {3}}", "_,3(a;#c/a;#e)"),             # 해설 45쪽 — 첨자 든 분수
    (r"\log_ {2} 2 (x - 2)", "_,2(#b8x9#b0)"),                             # 본문 29쪽 — 수 × 괄호
])
def test_로그_진수가_분수나_곱이면_묶는다(latex, brf):
    assert convert_latex(latex) == _b(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"\frac {3}{2 \overline {{\mathrm{AE}}}}", "(#b@c,,ae)/#c"),          # 해설 34쪽
    (r"\frac {\overline {{\mathrm{DE}}} ^ {2} + \overline {{\mathrm{BE}}} ^ {2} - \overline {{\mathrm{BD}}} ^ {2}}"
     r"{2 \times \overline {{\mathrm{DE}}} \times \overline {{\mathrm{BE}}}}",
     "(#b*@c,,de*@c,,be)/(@c,,de~#b5@c,,be~#b9@c,,bd~#b)"),               # 해설 33쪽 코사인 법칙
    (r"\frac {\overline {\mathrm{AC}} \times \overline {\mathrm{BD}}}{\overline {\mathrm{AB}}}", "@c,,ab/(@c,,ac*@c,,bd)"),  # 해설 35쪽
    (r"\frac {\overline {{\mathrm{AM}}}}{\overline {{\mathrm{AE}}}}", "@c,,ae/@c,,am"),   # 해설 34쪽 — 선분 하나는 안 묶음
])
def test_분수_칸이_선분_낀_곱이면_묶는다(latex, brf):
    # 제7항 3호(3149행) 분모나 분자가 곱이면 묶음 괄호(예 3160 · 3164행 `(ab)/#a` · `#e/(ab)`).
    # 셀만 맞댄다: 수 뒤 선분 앞 빈칸(`2 \overline`)은 원장 M-14 범위 밖이라 아직 남는다(gold 는 붙임).
    assert convert_latex(latex).replace("⠀", "") == _b(brf)


@pytest.mark.parametrize("latex,brf", [
    (r"\frac {| 4 \times 0 - 0 + 1 |}{\sqrt {4 ^ {2} + (- 1) ^ {2}}}", ">(#d~#b589#a0~#b)/|#d*#j9#j5#a|"),   # 본문 21쪽
    (r"\frac {| x - 1 |}{x - 1}", "(x9#a)/|x9#a|"),                       # 절댓값 하나뿐인 분자는 안 묶음
])
def test_절댓값_하나뿐인_분수_칸은_묶지_않는다(latex, brf):
    # 제7항 3호는 곱 · 다항식만 묶는다. 막대 안 ± 는 최상위가 아니다.
    assert convert_latex(latex) == _b(brf)


def test_절댓값_뒤에_항이_더_있으면_다항식이라_묶는다():
    # 제7항 3호(3149행) — `|f(x)| - f(x)` 는 다항식이다.
    assert convert_latex(r"\frac {| f (x) | - f (x)}{x - a}").replace("⠀", "") == _b("(x9a)/(|f8x0|9f8x0)")


@pytest.mark.parametrize("latex,brf", [
    (r"\frac {1}{- 9} - \frac {1}{- 5}", "(9#i)/#a9(9#e)/#a"),           # 해설 53쪽 — 원장 M-15(관행)
    (r"\frac {1}{4} \left(- \frac {1}{9} - \frac {1}{7}\right)", "#d/#a89#i/#a9#g/#a0"),   # 같은 쪽 — 분수 앞 부호는 그대로
])
def test_음수_분모는_묶는다(latex, brf):
    assert convert_latex(latex) == _b(brf)


def test_관계_기호가_든_괄호는_진수가_아니다():
    # 해설 12쪽 gold `_,2(89x0)`8x99#j0` — `(x<0)` 은 조건이다. 셀만 맞댄다(열 사이 칸은 이 과제 밖).
    lx = r"g (x) = \left\{ \begin{array}{l l} \log_ {2} (- x) & (x <   0) \\ \log_ {2} x & (x > 0) \end{array} \right."
    assert convert_latex(lx).replace("⠀", "") == _b("g8x0337'_,2(89x0)8x99#j0_,2x8x55#j0,7")


def test_로그가_든_괄호는_진수가_아니다():
    # 해설 7쪽 — 다음 줄이 `3(\log_{6} 2)^{2}` 라 괄호는 따로 곱하는 인수다(진수는 2 뿐).
    assert convert_latex(r"\log_ {6} 2 (6 \log_ {6} 2 - \log_ {3} 6)").startswith(_b("_,6#b8"))


@pytest.mark.parametrize("latex,brf", [
    (r"| 2 x + 7 | - 8", "|#bx5#g|9#h"),                                   # 제21항 예(3602행 `\#bx5#g\9#h`)
    (r"\| f \| = \int_ {0} ^ {1} | f (x) | d x", "||f||33!;#j`#a`|f8x0|dx"),   # 제28항 예(3693행)
    (r"\frac {| 4 \times 0 - 0 + 1 |}{\sqrt {4 ^ {2} + (- 1) ^ {2}}} = \frac {1}{\sqrt {17}} = \frac {\sqrt {17}}{17}",
     ">(#d~#b589#a0~#b)/|#d*#j9#j5#a|33>#ag/#a33#ag/>#ag"),                 # 본문 21쪽
    (r"\left| \log_ {a} \frac {1}{a ^ {2}} \right| = | \log_ {a} a ^ {- 2} | = | - 2 \log_ {a} a | = 2",
     "|_;a(a~#b/#a)|33|_;aa~9#b|33|9#b_;aa|33#b"),                        # 해설 9쪽
])
def test_닫는_막대_뒤_기호도_앞뒤를_붙인다(latex, brf):
    # 제45항 연산 · 비교 기호는 앞뒤를 붙인다. 닫는 막대(⠳)와 다음 기호가 칸을 두고 잇달면 다음 기호 뒤 칸이 남았다.
    assert convert_latex(latex) == _b(brf)
