"""규정이 붙여 적으라는 연산자에 원문 공백이 남던 문제 (2026-08-17).

규정 예시에 공백이 없다.
    제2항 붙임 곱셈점   6·9      #f"#i
    제4항 1호 같지않다   y≠0      y.33#j
반대로 제15항 일반연산(⊕⊖⊗∗∘)과 제29~32항 물결 계열은 "앞뒤를 한 칸씩 띄어 쓴다"이므로
건드리면 안 된다. 실측 공백 낀 붙임 대상 540건(cdot 282 · neq 225 · equiv 33).

관계 · 기하 기호(제34항 ∼ ≁ · 제41항 ⊥ · 제42항 ∽ · 제44항 ∥)도 규정 예시가 붙여 적는데, LaTeX 명령으로
오면 원문 칸이 남았다(2026-10-27). 물결아래등호 ≅(제32항)는 끝 두 셀이 등호와 같아 뒤 칸이 지워졌다.
"""
import pytest

from semojum_braille.encoder.kor_math_rules import convert_latex
from semojum_braille.encoder.translator import translate_tagged_text


@pytest.mark.parametrize("latex,expected", [
    (r"a \cdot b", "⠁⠐⠃"),        # 제2항 붙임
    (r"a \cdot 3", "⠁⠐⠼⠉"),
    (r"a \neq b", "⠁⠨⠒⠒⠃"),       # 제4항 1호
    (r"y \neq 0", "⠽⠨⠒⠒⠼⠚"),
])
def test_붙임_연산자는_공백을_지운다(latex, expected):
    assert convert_latex(latex) == expected


@pytest.mark.parametrize("latex,expected", [
    (r"a \sim b", "⠁⠈⠔⠃"),                                      # 제34항 1 `a∼b` = A@9B (재추출 3718행)
    (r"a \nsim b", "⠁⠨⠈⠔⠃"),                                    # 제34항 2 `a∼/b` = A.@9B (3722행)
    (r"\mathrm{AB} \perp \mathrm{DE}", "⠠⠠⠁⠃⠴⠄⠠⠠⠙⠑"),            # 제41항 `AB⊥DE` = ,,AB0',,DE (3777행)
    (r"\triangle ABC \backsim \triangle A'B'C'", "⠸⠬⠠⠠⠁⠃⠉⠠⠄⠸⠬⠠⠠⠁⠤⠃⠤⠉⠤"),  # 제42항 _+,,ABC,'_+,,A-B-C- (3779행)
    (r"\mathrm{AB} \parallel \mathrm{CD}", "⠠⠠⠁⠃⠰⠆⠠⠠⠉⠙"),        # 제44항 `AB⫽CD` = ,,AB;2,,CD (3785행)
    (r"\sim b", "⠈⠔⠃"),                                          # 식 머리(왼쪽 글자 없음)에서도 깨지지 않는다
])
def test_관계_기하_기호는_앞뒤를_붙인다(latex, expected):
    assert convert_latex(latex) == expected


def test_한글_곁_물결은_칸을_겹치지_않는다():
    """국어 묶음 사이 범위 물결은 제46항 몫이라 원문 칸을 둔다. 붙였다가 sentinel 복원이 칸을 다시 넣어 두 칸이 됐다."""
    out = translate_tagged_text(r"<!수식>\text{가 구간 A} \sim \text{B 구간}<!/수식>")
    assert "⠈⠔" in out and "⠀⠀" not in out


@pytest.mark.parametrize("latex,expected", [
    (r"x \oplus y", "⠭⠀⠸⠢⠀⠽"),    # 제15항 "기호의 앞뒤를 한 칸씩 띄어 쓴다"
    (r"a \circ b", "⠁⠀⠸⠴⠀⠃"),
    (r"a \approx b", "⠁⠀⠈⠔⠈⠔⠀⠃"),  # 제29항 "그 앞뒤를 한 칸씩 띄어 쓴다"
    (r"A \cong B", "⠠⠁⠀⠈⠔⠒⠒⠀⠠⠃"),  # 제32항 `A≅B` = ,a`@933`,b (재추출 3705행, 백틱은 빈칸)
    (r"A \cap B", "⠠⠁⠀⠩⠀⠠⠃"),
])
def test_규정이_띄우라는_칸은_지킨다(latex, expected):
    assert convert_latex(latex) == expected


@pytest.mark.parametrize("text", ["사회·문화", "가·나·다"])
def test_한글_가운뎃점은_안_건드린다(text):
    """실측 14,031건이다 — 곱셈점과 같은 문자라 넓게 잡으면 본문이 깨진다."""
    assert translate_tagged_text(text) == translate_tagged_text(text.replace("·", "·"))
    assert "⠐⠆" in translate_tagged_text(text)
