"""홀로 선 글자열을 약자로 줄이면 다른 낱말로 읽히는 자리 · -ing 단축형(#1626).

조항은 `braille-source/text/통일영어점자 규정_UEB2013.txt` 행 번호다. 낱말은 규정 예문이 아니라 **지어낸** 것이다 — 목록을
외운 것이 아니라 규칙이 처음 보는 낱말에 통하는지를 본다. 기대 점자는 조문에서 손으로 옮겼다.
"""
import pytest

from semojum_braille.encoder import eng_braille as E
from semojum_braille.encoder.translator import translate_with_breaks


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0]).strip("⠀")


@pytest.mark.parametrize("word, cells", [
    # 10.9 단축형 표(5450~5480행)의 -ing 꼴
    ("receiving", "⠗⠉⠧⠛"), ("rejoicing", "⠗⠚⠉⠛"), ("conceiving", "⠒⠉⠧⠛"),
])
def test_ing_단축형(word, cells):
    assert E.translate(word) == cells


@pytest.mark.parametrize("text, cells", [
    # 10.4.2(4609~4622행) 홀로 선 강약자 글자열은 단어 약자(out · child)로 읽혀 글자대로
    ("ou", "⠕⠥"), ("Ch", "⠠⠉⠓"),
    # 10.9.4(5622~5632행) 묶음 약자가 단축형의 일부가 되면 안 쓴다 — chn 은 children(⠡⠝) · mch 는 much(⠍⠡) 로 읽힌다
    ("chn file", "⠉⠓⠝⠀⠋⠊⠇⠑"), ("mch", "⠍⠉⠓"),
    # 10.6.9(5019~5027행) 홀로 선 en 은 enough(⠢) 로 읽힌다
    ("en masse", "⠑⠝⠀⠍⠁⠎⠎⠑"),
    # 10.9.6(5653~5659행) 첫머리가 아닌 brl · grt 는 ⠰⠰ 를 앞세우고 낱말 안 약자를 안 쓴다
    ("Kobrlak", "⠰⠰⠠⠅⠕⠃⠗⠇⠁⠅"), ("zigrtin", "⠰⠰⠵⠊⠛⠗⠞⠊⠝"),
])
def test_다른_낱말로_읽히면_글자대로(text, cells):
    assert _tr(text) == cells


@pytest.mark.parametrize("text, cells", [
    # 2.6.1~2.6.3(1345~1426행) 글자 · 숫자 · 마침표에 붙으면 홀로 서지 않는다 — 약자를 그대로 쓴다
    ("7th", "⠼⠛⠹"), ("www.sch.kr", "⠺⠺⠺⠲⠎⠡⠲⠅⠗"),
    # 홀로 서도 다른 낱말로 안 읽히면 그대로(`Shhh` 는 강약자 하나가 아니다)
    ("Shhh", "⠠⠩⠓⠓"),
])
def test_홀로_서지_않거나_안_읽히면_약자_그대로(text, cells):
    assert _tr(text) == cells


def test_한국어_문장_속도_같다():
    assert "⠴⠕⠥⠲" in _tr("모음 ou 소리")
