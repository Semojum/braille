"""따옴표 · 괄호 안쪽과 빗금 둘레의 가는 띄움(U+2009 등)을 걷는다(#1519).

기대 점형은 「한국 점자 규정」(`한국 점자 규정_재추출.txt`) 예문이다: 제54항 2412행 예문 안의 `‘시작이 반이다.’` =
`,8,o.ao`~3oi40'` · 제52항 [붙임 1] `먹이다/먹히다` = `e?oi_/e?joi`(2371~2372행) · [붙임 2] `1,000원/개` = `#a1jjjp3_/@r`
(2380~2381행) · 「점자 도서 제작 지침」 제2장 7. 번호 체계 예 `1)` = `#a,0`(1249행 묵자 · 1258행 점자).
묵자가 그 자리에 가는 띄움을 두어도 같아야 한다. 그 밖의 문장은 지어낸 것이다.
"""
from __future__ import annotations

import pytest

from semojum_braille.encoder import translator as T
from semojum_braille.encoder.translator import translate_body
from braille_ascii import ascii_to_unicode

def _br(text: str) -> str:
    return "".join(translate_body(text)[0])


@pytest.mark.parametrize("src, brf", [
    ("‘\u2009시작이 반이다.\u2009’", ",8,o.ao`~3oi40'"),
    ("‘\u2006시작이 반이다.’", ",8,o.ao`~3oi40'"),
    ("먹이다\u2009/\u2009먹히다", "e?oi_/e?joi"),
    ("1,000원\u2005/개", "#a1jjjp3_/@r"),
    ("1\u2005)", "#a,0"),          # 목록 번호 — 문항 번호 마침표(_QNUM_RE)가 띄움을 번호 뒤 빈칸으로 읽었다
])
def test_규정_예문과_같게_적는다(src, brf):
    assert _br(src) == ascii_to_unicode(brf, backtick="space")


@pytest.mark.parametrize("src, want", [
    ("1\u2005) 처음 할 일", "1) 처음 할 일"),       # 목록 번호 — 빈칸이 끼면 없는 마침표까지 붙었다
    ("「\u20092\u2009」 둘째 뜻", "「2」 둘째 뜻"),
    ("[그림:\u2009봄.jpg\u2009]", "[그림:\u2009봄.jpg]"),  # 쌍점 뒤 띄움은 이 함수 몫이 아니다
])
def test_안쪽_띄움을_걷는다(src, want):
    assert T._attach_bracket_slash(src) == want


@pytest.mark.parametrize("src", [
    "(\u2009\u2009)을 채우시오",      # 채울 칸 — 안이 빈 괄호
    "‘\u2009’ 표",
    "( 1 ) 보통 빈칸",                  # U+0020 은 안 건드린다
    "‘\u2009<!강조>봄<!/강조>’",        # 태그 바로 앞
    "가 / 나",
])
def test_그대로_둔다(src):
    assert T._attach_bracket_slash(src) == src
