"""국어 문장 속 로마자 단위 위첨자(#1572).

기대값은 「한국 점자 규정」 제68항 · 제69항 · 과학 편 제30항 예문(재추출 행 번호)이거나 그 조항 꼴로 지은 문장이다.
교재 줄은 쓰지 않았다.
"""
import pytest

from semojum_braille.encoder.translator import translate_with_breaks


def _t(text: str) -> str:
    return "".join(translate_with_breaks(text)[0])


@pytest.mark.parametrize("text,want", [
    ("kgf/m²", "⠴⠅⠛⠋⠸⠌⠍⠘⠼⠃"),                                # 과학 편 제30항 5037행 `0kgf_/m ^ # b`
    ("넓이는 약 3만km²이다", "⠉⠞⠃⠕⠉⠵⠀⠜⠁⠀⠼⠉⠀⠑⠒⠴⠅⠍⠘⠼⠃⠕⠊"),   # 끝이 위첨자라 종료표 없음(제68항 `㎡` 2655행)
    ("면적(m²)과", "⠑⠡⠨⠹⠦⠄⠴⠍⠘⠼⠃⠠⠴⠈⠧"),                      # 괄호 속 단위 이름표는 글 괄호다
    ("압력 1 kgf/m²이다", "⠣⠃⠐⠱⠁⠀⠼⠁⠀⠴⠅⠛⠋⠸⠌⠍⠘⠼⠃⠕⠊"),          # 띄어쓰기는 묵자를 따른다(제69항 2682행)
    ("가속도는 9.8 m/s²이다", "⠫⠠⠭⠊⠥⠉⠵⠀⠼⠊⠲⠓⠀⠴⠍⠸⠌⠎⠘⠼⠃⠕⠊"),   # 수가 9. 과 8 로 쪼개지지 않는다
])
def test_단위_위첨자는_로마자표를_앞세운_한_구간이다(text, want):
    assert _t(text) == want


@pytest.mark.parametrize("text,unit_form", [("x²+y²=1", "⠴⠭"), ("m²-4m+3=0", "⠴⠍"), ("2m²+3", "⠴⠍")])
def test_식_속_위첨자는_수식으로_둔다(text, unit_form):
    assert unit_form not in _t(text)


def test_수식_태그_안은_건드리지_않는다():
    assert "⠴⠍" not in _t("<!수식>(m²)<!/수식>")
