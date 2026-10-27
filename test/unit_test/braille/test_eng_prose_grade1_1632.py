"""한글 없는 영어 산문 줄의 1종 지시자 ⠰(#1632) — 통일영어점자 10.9.5(`통일영어점자 규정_UEB2013.txt` 5634~5651행).

홀로 선 낱자 · 낱자열이 단어 약자 · 단축형과 셀이 같으면 앞에 ⠰ 를 적는다. 문장은 지어낸 것이고 기대 점자는 조문에서
손으로 옮겼다(대화 말머리 꼴은 gold EBS-E26-008 의 `;,W3` · `;,M3` 와 같은 꼴).
"""
import pytest

from semojum_braille.encoder.translator import translate_with_breaks


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0]).strip("⠀")


@pytest.mark.parametrize("text, cells", [
    # 대화 말머리 — W 는 will, M 은 more 로 읽힌다
    ("W: Tom, we can go.", "⠰⠠⠺⠒⠀⠠⠞⠕⠍⠂⠀⠺⠑⠀⠉⠀⠛⠲"),
    # 문장 속 홑 낱자 — B 는 But 으로 읽힌다 · 여는 따옴표 뒤도 홀로 선다(2.6.2)
    ("Option B was fine.", "⠠⠕⠏⠰⠝⠀⠰⠠⠃⠀⠴⠀⠋⠔⠑⠲"),
    #   (then = !n, 10.10.3 예 5702행)
    ('She said "D is red" then.', "⠠⠩⠑⠀⠎⠙⠀⠦⠰⠠⠙⠀⠊⠎⠀⠗⠫⠴⠀⠮⠝⠲"),
    #   닫는 따옴표(점자로 먼저 바뀐 셀)를 건너 빈칸이면 홀로 선다(2.6.3) · there = "!(10.7)
    ('He wrote "B" there.', "⠠⠓⠑⠀⠺⠗⠕⠞⠑⠀⠦⠰⠠⠃⠴⠀⠐⠮⠲"),
    # 낱자열이 단축형(sd = said)과 같다
    ("sd is short for it", "⠰⠎⠙⠀⠊⠎⠀⠩⠕⠗⠞⠀⠿⠀⠭"),
])
def test_영어_산문_줄의_1종_지시자(text, cells):
    assert _tr(text) == cells


@pytest.mark.parametrize("text, cells", [
    # 약자로 안 읽히는 낱자(a · I)와 라벨만 있는 줄은 그대로
    ("I saw a cat.", "⠠⠊⠀⠎⠁⠺⠀⠁⠀⠉⠁⠞⠲"),
    ("C  D  E", "⠠⠉⠀⠀⠠⠙⠀⠀⠠⠑"),
])
def test_안_적는_자리(text, cells):
    assert _tr(text) == cells


@pytest.mark.parametrize("text, cells", [
    # 2.6.3(1406~1430행) 마침표 · & 너머가 글자면 홀로 서지 않는다 — p(people) · Q(quite) · J(just) 앞에 ⠰ 없음.
    #   6.3.1 예 `7:30 a.m.` = #g3#cj a4m4(2927행) 의 m 과 같은 자리, 2.6.2 끝 `&c` = @&c(1392행)
    ("Come at 7 p.m. sharp.", "⠠⠉⠕⠍⠑⠀⠁⠞⠀⠼⠛⠀⠏⠲⠍⠲⠀⠩⠜⠏⠲"),
    ("Read the Q&A page.", "⠠⠗⠂⠙⠀⠮⠀⠠⠟⠈⠯⠠⠁⠀⠏⠁⠛⠑⠲"),
    ("Ask J.Doe Studio now.", "⠠⠁⠎⠅⠀⠠⠚⠲⠠⠙⠕⠑⠀⠠⠌⠥⠙⠊⠕⠀⠝⠪⠲"),
])
def test_문장_부호_너머가_글자면_홀로_서지_않는다(text, cells):
    assert _tr(text) == cells


def test_표_줄은_산문이_아니다():
    # 표 선형 초안은 한 행을 한 줄로 넘긴다. 칸은 라벨이라 1종 지시자를 켜지 않는다(원장 C-99 순수 로마자 줄 보류).
    assert "⠰" not in _tr("<!행><!칸>k<!칸>kk<!칸>d<!칸>tt<!/행>")
    assert "⠰" not in _tr("kk | k | d | tt")             # 선형 초안은 칸을 ` | ` 로 잇는다
