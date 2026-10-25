"""영어 낱말 속 아포스트로피 — 로마자 구간을 안 끊고, 단어 약자는 UEB 10.1.2 · 10.2.2 대로(#1543).

「한국 점자 규정」 제32항(재추출 1650행): 로마자표와 종료표 사이는 「통일영어점자 규정」대로 적는다.
UEB 2.6.4: 안에 아포스트로피가 든 낱말은 한 낱말이다. 10.1.2 · 10.2.2: 아포스트로피 뒤가 d · ll · re · s · t · ve 일 때만
단어 약자를 쓴다. 기대값은 전부 `통일영어점자 규정_UEB2013.txt`(ICEB 2nd Ed. 2013) 행에서 옮겼다(행 번호를 옆에 적는다).
종전엔 문자표가 `'` 를 먼저 ⠄ 로 바꿔 `그는 can't라고` 가 ⠴⠉⠁⠝⠲⠄⠴⠞⠲ 로 갈렸다.
"""
import pytest

from semojum_braille.encoder.translator import _INNER_APOS_HOLD_RE, translate_with_breaks


def _cells(text: str) -> str:
    return "".join(translate_with_breaks(text)[0]).strip("⠀")


@pytest.mark.parametrize("word,cells", [
    ("it'd", "⠭⠄⠙"), ("you'd", "⠽⠄⠙"), ("it'll", "⠭⠄⠇⠇"), ("that'll", "⠞⠄⠇⠇"),   # 10.1.2 예(4405~4410행)
    ("you're", "⠽⠄⠗⠑"), ("people's", "⠏⠄⠎"), ("can't", "⠉⠄⠞"), ("you've", "⠽⠄⠧⠑"),
    ("d'you", "⠙⠄⠽⠳"), ("t'do", "⠞⠄⠙⠕"), ("t'have", "⠞⠄⠓⠁⠧⠑"),                    # 뒤 조각은 단어 약자 아님(4398행)
    ("this'd", "⠹⠄⠙"), ("which'll", "⠱⠄⠇⠇"), ("still's", "⠌⠄⠎"), ("which've", "⠱⠄⠧⠑"),  # 10.2.2 예(4482~4485행)
    ("this'n", "⠹⠊⠎⠄⠝"),                                                              # 10.2.2 But(4486행)
    ("mustn't", "⠍⠌⠝⠄⠞"),                                                             # Appendix 1(9960행)
    ("O'Connor", "⠠⠕⠄⠠⠉⠕⠝⠝⠕⠗"), ("Ch'ing", "⠠⠡⠄⠬"),                                 # Appendix 2(9986 · 9401행)
    ("be'ave", "⠃⠑⠄⠁⠧⠑"), ("e'er", "⠑⠄⠻"),                                           # Appendix 2(9255 · 9579행)
])
def test_영어만_있는_낱말(word, cells):
    assert _cells(word) == cells


@pytest.mark.parametrize("word,cells", [
    ("can't", "⠉⠄⠞"), ("child's", "⠡⠄⠎"), ("I'm", "⠠⠊⠄⠍"), ("this'n", "⠹⠊⠎⠄⠝"), ("O'Connor", "⠠⠕⠄⠠⠉⠕⠝⠝⠕⠗"),
])
def test_국어_문장_속에서도_로마자_구간_하나(word, cells):
    """로마자표 ⠴ + 낱말 + 종료표 ⠲ + 라고(제29항 · 제32항). 종전엔 아포스트로피 자리에서 구간을 닫고 다시 열었다."""
    assert "⠴" + cells + "⠲⠐⠣⠈⠥" in _cells(f"그는 {word}라고 말했다.")


@pytest.mark.parametrize("text", ["각 BA'C에서", "점 A'에서", "f'(x)", "A'B'", "Ⅰ'"])
def test_수학_프라임은_맡기지_않는다(text):
    """dev · val 입력의 한글 줄 `X'Y` 19곳(6쪽)이 전부 수학 프라임이다. 뒤가 홑 대문자 · 한글 · 괄호면 영어 낱말로 묶지 않는다."""
    assert _INNER_APOS_HOLD_RE.search(text) is None
