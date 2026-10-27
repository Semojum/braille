"""아래칸 단어 약자(be · were · his · was · in · enough)를 문장 부호 · 붙임표 옆에서 어떻게 적나(#1628).

조항은 `braille-source/text/통일영어점자 규정_UEB2013.txt` 행 번호, 한국어 문장 속은 「한국 점자 규정」 제37항 [붙임].
낱말 · 문장은 지어낸 것이고 기대 점자는 조문에서 손으로 옮겼다.
"""
import pytest

from semojum_braille.encoder.translator import translate_with_breaks


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0]).strip("⠀")


@pytest.mark.parametrize("text, cells", [
    # 10.5.3(4724~4756행) in 은 그 줄에 1 · 4점 셀이 있으면 어디서나 약자 — 붙임표로 이은 합성어 속
    ("plug-in", "⠏⠇⠥⠛⠤⠔"), ("sign-in", "⠎⠊⠛⠝⠤⠔"),
    # 10.5.4(4762~4775행) 문장 부호에 닿은 줄에 1 · 4점 셀이 없으면 풀어 쓴다
    ("Log in.", "⠠⠇⠕⠛⠀⠊⠝⠲"), ("It is enough.", "⠠⠭⠀⠊⠎⠀⠢⠳⠣⠲"),
    # 10.5.1(4663~4700행) be · were · his · was 는 아래 점만 쓰는 부호(붙임표 · 쉼표)에 닿으면 풀어 쓴다
    ("were-wolf", "⠺⠻⠑⠤⠺⠕⠇⠋"), ("He was, I think, late.", "⠠⠓⠑⠀⠺⠁⠎⠂⠀⠠⠊⠀⠹⠔⠅⠂⠀⠇⠁⠞⠑⠲"),
    # 괄호는 4점이 있는 부호라 닿아도 약자(10.5.1 `(not his)` = "<n 8">)
    ("We saw it (was it new).", "⠠⠺⠑⠀⠎⠁⠺⠀⠭⠀⠐⠣⠴⠀⠭⠀⠝⠑⠺⠐⠜⠲"),
])
def test_한글_없는_영어_줄(text, cells):
    assert _tr(text) == cells


@pytest.mark.parametrize("text, roman", [
    # 제37항 [붙임] — 로마자 종료표 앞은 풀어 쓴다
    ("기호는 plug-in 이다", "⠴⠏⠇⠥⠛⠤⠊⠝⠲"),
    # 붙임표로 이은 합성어 속은 종료표 앞이 아니다 — 약자
    ("기호는 son-in-law 이다", "⠴⠎⠕⠝⠤⠔⠤⠇⠁⠺⠲"),
])
def test_한국어_문장_속(text, roman):
    assert roman in _tr(text)
