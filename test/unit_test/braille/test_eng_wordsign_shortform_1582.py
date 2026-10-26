"""영어 약자 두 자리(#1582) — 「한국 점자 규정」 제37항 29낱말 · 「통일영어점자 규정」 10.9.3 긴 낱말 안 단축형.

제37항(정본 1795~1851행)은 로마자표 바로 뒤에서 단어 약자를 풀어 쓰는 낱말을 29개로 든다. 강약자 child · shall · this ·
which · out · still 은 목록에 없어 약자를 쓴다(2027 gold 10권 307곳 약자 · 풀어씀 0). 10.9.3(UEB2013 5576~5621행)은
braille · great 을 어디서나, children 을 뒤가 모음 · y 가 아니면, blind · first · friend · good · letter · little · quick 을
낱말 첫머리이고 뒤가 모음 · y 가 아니면 긴 낱말 안에서도 단축형으로 적게 한다. ★ 입력은 흔한 낱말로만 짰다.
"""
import pytest

from semojum_braille.encoder import eng_braille as E
from semojum_braille.encoder.translator import translate_with_breaks

PRE, POST = "⠈⠕⠚⠥⠉⠵⠀⠴", "⠲⠀⠕⠊"      # 기호는 ⠴ … ⠲ 이다


def _in_sentence(word: str) -> str:
    return "".join(translate_with_breaks(f"기호는 {word} 이다")[0])


def test_제37항_목록은_단어_약자_29낱말이다():
    assert len(E._R37_WORDS) == 29 and E._R37_WORDS <= set(E.WORDSIGNS)


@pytest.mark.parametrize("word,cells", [("child", "⠡"), ("shall", "⠩"), ("this", "⠹"), ("which", "⠱"),
                                        ("out", "⠳"), ("still", "⠌")])
def test_강약자는_로마자표_바로_뒤에서도_약자다(word, cells):
    assert _in_sentence(word) == PRE + cells + POST


@pytest.mark.parametrize("word,cells", [("people", "⠏⠑⠕⠏⠇⠑"), ("rather", "⠗⠁⠮⠗")])   # 정본 1799~1800 · 1811~1812행
def test_제37항_낱말은_로마자표_바로_뒤에서_풀어_쓴다(word, cells):
    assert _in_sentence(word) == PRE + cells + POST


@pytest.mark.parametrize("word,cells", [
    ("greatly", "⠛⠗⠞⠇⠽"),            # (a) great 어디서나
    ("grandchildren", "⠛⠗⠯⠡⠝"),      # (b) children 끝
    ("quickly", "⠟⠅⠇⠽"),              # (c) 첫머리 + 자음
    ("blindness", "⠃⠇⠰⠎"),            # (c) 뒤 조각은 낱말 첫머리가 아니라 끝 묶음표(ness)를 쓴다
    ("friends", "⠋⠗⠎"),
    ("littler", "⠇⠇⠗"),
])
def test_긴_낱말_안_단축형(word, cells):
    assert E.translate_word(word) == cells


@pytest.mark.parametrize("word,cells", [
    ("blinded", "⠃⠇⠔⠙⠫"),             # 뒤가 모음
    ("goodies", "⠛⠕⠕⠙⠊⠑⠎"),           # 뒤가 모음
    ("bisquick", "⠃⠊⠎⠟⠥⠊⠉⠅"),         # 첫머리가 아님
    ("unfriendly", "⠥⠝⠋⠗⠊⠢⠙⠇⠽"),      # 첫머리가 아님
])
def test_조건_밖은_단축형을_안_쓴다(word, cells):
    assert E.translate_word(word) == cells
