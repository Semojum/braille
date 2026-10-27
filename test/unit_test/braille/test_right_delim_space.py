"""수식 안 LaTeX 빈칸이 닫는 크기 괄호 앞 · 델연산자 뒤에 점자 빈칸으로 남던 자리."""
import semojum_braille.encoder.translator  # noqa: F401  (한글 훅 등록 — import 부작용)
from semojum_braille.encoder.kor_math_rules import convert_latex


def test_델연산자_규정_예문():
    # 「수학 점자」 제55항 예(재추출 4012~4020행) `∇f=(f/x₁, f/x₂, ⋯, f/xₙ)` = _%F338X;#a/F"`X;#b/F"`,,," / X;N/F0
    assert convert_latex(r"\nabla f = \left( \frac{f}{x_1},\ \frac{f}{x_2},\ \cdots, \frac{f}{x_n} \right)") == (
        "⠸⠩⠋⠒⠒⠦⠭⠰⠼⠁⠌⠋⠐⠀⠭⠰⠼⠃⠌⠋⠐⠀⠠⠠⠠⠐⠀⠭⠰⠝⠌⠋⠴")


def test_닫는_크기_괄호_앞_빈칸은_없다():
    assert convert_latex(r"\left( x \right)^{2}") == convert_latex(r"\left(x\right)^{2}")
    assert "⠀⠠⠾" not in convert_latex(r"\left[ \frac{1}{2}x^{2} \right]_{0}^{1}")
