"""화살표는 앞뒤를 한 칸씩 띄우고, 숫자 사이 쌍점과 가운뎃점은 둘레의 가는 띄움을 걷는다(#1517).

기대 점형은 「한국 점자 규정」(`한국 점자 규정_재추출.txt`) 예문이다: 제70항 `부산 → 서울` = `~ml3`3o`,s&`(2790~2791행) ·
`한글 ↔ 일본어 번역` = `j3@!`{3o`o1~(s`~):a`(2794~2795행) · 제51항 [다만 2] `오전 10:20` = `u.)`#aj"1#bj`(2357~2358행) ·
제50항 `정치·경제` = `.];o"2@].n`(2328~2329행) · 제51항 본칙 `일시: 2006년 2월 28일 13시` = `o1,o"1`#bjjf…`(2348~2350행, #1546).
묵자가 화살표를 붙여 쓰거나 둘레에 가는 띄움(U+2009)을 두거나 쌍점 앞에 빈칸을 두어도 같아야 한다.
그 밖의 문장은 지어낸 것이다.
"""
from __future__ import annotations

import pytest

from semojum_braille.encoder import translator as T
from semojum_braille.encoder.translator import translate_body
from braille_ascii import ascii_to_unicode


def _br(text: str) -> str:
    return "".join(translate_body(text)[0])


@pytest.mark.parametrize("src, brf", [
    ("부산→서울", "~ml3`3o`,s&"),
    ("부산 →서울", "~ml3`3o`,s&"),
    ("한글↔일본어 번역", "j3@!`{3o`o1~(s`~):a"),
    ("오전 10\u2009:\u200920", 'u.)`#aj"1#bj'),
    ("정치\u2009·\u2009경제", '.];o"2@].n'),
    ("일시 : 2006년 2월 28일 13시", 'o1,o"1`#bjjf`c*`#bp1`#bho1`#ac,o'),   # 쌍점 앞 빈칸(#1546)
])
def test_규정_예문과_같게_적는다(src, brf):
    assert _br(src) == ascii_to_unicode(brf, backtick="space")


def test_줄머리_여는_괄호_따옴표_바로_뒤는_앞을_붙인다():
    assert T._space_arrow("다음 단계(→셋째 쪽)") == "다음 단계(→ 셋째 쪽)"
    assert T._space_arrow("→다음 단계") == "→ 다음 단계"
    assert T._space_arrow("첫 단계\n→다음 단계") == "첫 단계\n→ 다음 단계"
    assert T._space_arrow("‘→’ 표시") == "‘→’ 표시"


@pytest.mark.parametrize("src", [
    "<!수식>A→B<!/수식>",          # 수식은 수학 점자 경로가 맡는다
    "<!칸>→<!칸>",                  # 표 칸 경계
    "기체 CO₂↑ 와 침전 AgCl↓",      # 과학 점자 제18항 2 — 분자식에 붙인다
    "봄 → 여름",
])
def test_화살표_그대로_둔다(src):
    assert T._space_arrow(src) == src


@pytest.mark.parametrize("src", [
    "학생 2:\u2009이어서 말한다",     # 제51항 본 규정 — 쌍점 뒤 한 칸
    "·\u2009목록 머리",               # 줄머리 목록 표시
    "<!칸>·\u2009목록 머리",
])
def test_쌍점_가운뎃점_그대로_둔다(src):
    assert T._attach_colon_middot(src) == src


def test_한글_뒤_쌍점은_앞_빈칸을_걷는다():
    """제51항 본칙 — 앞은 붙이고 뒤는 한 칸(#1546). gold 를 잰 꼴(앞이 한글)만 걷는다."""
    assert T._attach_colon_middot("자료 : 설명") == "자료: 설명"
    assert T._attach_colon_middot("가 : 나 : 다") == "가: 나: 다"
    assert T._attach_colon_middot("자료\u2009: 설명") == "자료: 설명"


@pytest.mark.parametrize("src", [
    "청군:백군",               # [다만 2] 대비 — 앞뒤 붙임 그대로
    "자료 :설명",              # 뒤가 붙은 꼴은 묵자 신호를 따른다
    "비는 1 : 2이다",          # 숫자 비 · 닫는 괄호 앞은 gold 를 안 쟀다
    "(넓이) : (넓이)",
])
def test_한글_뒤가_아니거나_뒤가_붙은_쌍점은_그대로_둔다(src):
    assert T._attach_colon_middot(src) == src
