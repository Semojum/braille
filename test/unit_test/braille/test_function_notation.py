"""함수 표기(「수학 점자」 제45항): 합성 ∘ 는 붙이고, 화살표 위 글자는 화살표 앞 · 아래 글자는 화살표 뒤에 적는다."""
import pytest

import semojum_braille.encoder.translator  # noqa: F401  (한글 훅 등록 — import 부작용)
from semojum_braille.encoder.kor_math_rules import convert_latex


@pytest.mark.parametrize("latex, expected", [
    (r"(g \circ f)(x) = g(f(x))", "⠦⠛⠸⠴⠋⠴⠦⠭⠴⠒⠒⠛⠦⠋⠦⠭⠴⠴"),           # 재추출 3795~3796행 8G_0F08X033G8F8X00
    (r"x \xrightarrow{f} y", "⠭⠀⠋⠒⠕⠀⠽"),                             # [붙임] 3799~3801행 X`F3O`Y
    (r"x \underset{g}{\overset{f}{\rightleftarrows}} y", "⠭⠀⠋⠪⠶⠕⠛⠀⠽"),  # 3802~3805행 X`F[7OG`Y
    (r"x \overset{f}{\underset{g}{\rightleftarrows}} y", "⠭⠀⠋⠪⠶⠕⠛⠀⠽"),  # 위 · 아래를 거꾸로 감싸도 같다
])
def test_규정_예문(latex, expected):
    assert convert_latex(latex) == expected


def test_일반연산_동그라미는_앞뒤_한_칸():
    # 제15항 5호 `a∘e=ae+a` = a`_0`e33ae5a. 함숫값을 부르는 `(…)(` 꼴이 아니면 합성으로 보지 않는다.
    assert convert_latex(r"a \circ b") == "⠁⠀⠸⠴⠀⠃"
