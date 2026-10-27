"""식 안의 한글 항(「수학 점자」 제6항 예): 한글 쪽 연산 기호 앞뒤 한 칸(제46항) · 근호 속 한글 묶음."""
from semojum_braille.encoder.translator import translate_with_breaks
from braille_ascii import ascii_to_unicode


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0])


def test_분수_속_한글_항():
    # 재추출 3134~3137행 `(자연수×자연수)/(자연수+자연수)=(1×2)/(1+2)` = _(.<*,m`5`.<*,m_)/_(.<*,m`*`.<*,m_)33(#a5#b)/(#a*#b)
    src = r"<!수식>\frac{\text{자연수}\times\text{자연수}}{\text{자연수}+\text{자연수}}=\frac{1\times 2}{1+2}<!/수식>"
    assert _tr(src) == ascii_to_unicode("_(.<*,m`5`.<*,m_)/_(.<*,m`*`.<*,m_)33(#a5#b)/(#a*#b)", backtick="space")


def test_근호_속_한글_항():
    # 재추출 3138~3140행 `표준편차=√분산` = d+.gd*;<`33>_(^gl3_)
    assert _tr("<!수식>표준편차=\\sqrt{분산}<!/수식>") == ascii_to_unicode("d+.gd*;<`33>_(^gl3_)", backtick="space")
