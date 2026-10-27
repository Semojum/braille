"""영어 낱말의 변형 글자를 통일영어점자 4.2 · 4.3 대로 적는다(#1620).

변형표는 글자 앞(4.2.1), 변형 글자는 약자에 안 든다(4.2.4), 대문자 낱말 모드를 안 끊는다(4.2.3), 합자는 ⠘⠖(4.3.1).
기대 점형은 `통일영어점자 규정_UEB2013.txt` 예문 줄이다(행 번호는 각 줄 주석). 아래 둘째 시험의 낱말은 지어낸 것이다 —
목록을 외운 것이 아니라 글자 규칙이라 처음 보는 낱말에도 통해야 한다.
"""
import pytest

from semojum_braille.encoder.translator import dropped_unknown, translate_tagged_text


def _tr(text: str) -> str:
    return translate_tagged_text(text).strip("⠀")


@pytest.mark.parametrize("text,want", [
    ("AOÛT", "⠠⠠⠁⠕⠘⠩⠥⠞"),                                      # 2385 ,,ao^%ut
    ("blessèd", "⠃⠨⠎⠘⠡⠑⠙"),                                      # 2390 b.s^*ed
    ("Général de Gaulle", "⠠⠛⠘⠌⠑⠝⠘⠌⠑⠗⠁⠇⠀⠙⠑⠀⠠⠛⠁⠥⠇⠇⠑"),             # 2391
    ("théâtre", "⠹⠘⠌⠑⠘⠩⠁⠞⠗⠑"),                                  # 2397 ?^/e^%atre (the 대신 th)
    ("señor", "⠎⠑⠘⠻⠝⠕⠗"),                                        # 2398 se^]nor
    ("Händel", "⠠⠓⠘⠒⠁⠝⠙⠑⠇"),                                    # 2399 ,h^3andel (and 를 안 쓴다)
    ("Cœur de Lion", "⠠⠉⠕⠘⠖⠑⠥⠗⠀⠙⠑⠀⠠⠇⠊⠕⠝"),                      # 2451 ,co^6eur de ,lion
    ("ŒDIPUS", "⠠⠠⠕⠘⠖⠑⠙⠊⠏⠥⠎"),                                  # 2461 ,,o^6edipus
])
def test_통일영어점자_예문대로_적는다(text, want):
    assert _tr(text) == want


@pytest.mark.parametrize("text,want", [
    ("bébé", "⠃⠘⠌⠑⠃⠘⠌⠑"),          # be 약자에 é 가 못 든다
    ("façade", "⠋⠁⠘⠯⠉⠁⠙⠑"),
    ("naïve", "⠝⠁⠘⠒⠊⠧⠑"),
])
def test_처음_보는_낱말에도_같은_규칙이다(text, want):
    assert _tr(text) == want


def test_대문자_구절_안의_변형_글자도_셀로_바뀐다():
    # 세 낱말 이상 대문자 구절은 `translate` 가 구절 셀을 따로 만든다(4.2.3: 변형표가 대문자 모드를 안 끊는다)
    assert _tr("NAÏVE PULP KIT") == "⠠⠠⠠⠝⠁⠘⠒⠊⠧⠑⠀⠏⠥⠇⠏⠀⠅⠊⠞⠠⠄"


def test_국어_문장_속_로마자_구간도_같다():
    assert "⠴⠎⠑⠘⠻⠝⠕⠗⠲" in _tr("기호는 señor 이다")


def test_점형이_없는_글자는_점자_밖_글자로_새지_않고_R17_로_센다():
    out = _tr("straße")
    assert all("⠀" <= c <= "⣿" for c in out)
    assert dropped_unknown("straße") == {"ß": 1}
