"""새 문단 첫 줄 3칸(「점자 자료 제작 지침」 2.1.1(1), 재추출 444행) — 레이아웃 자 R6 이 짚은 자리(#1532).

엔진 `build_pages` 는 들여쓰기 · 빈 줄을 넣지 않으므로 응답 `contents` 의 칸이 그대로 점자 면에 찍힌다.
문장은 지어낸 것이다(교재 줄을 넣지 않는다).
"""
from uuid import uuid4

from semojum_braille.encoder.layout_braille import LayoutBraille, _is_q_head, _q_blanks
from semojum_braille.schemas import BrailleOutput

A = "⠁⠃⠉"                      # 내용 셀은 판정과 무관하다
TOP = "⠿" + "⠛" * 30 + "⠿"
BOT = "⠿" + "⠶" * 30 + "⠿"


def _indents(lines: list[str], src: str, etype: str = "text") -> list[int]:
    bo = BrailleOutput(element_id=uuid4(), braille_lines=list(lines), corrected_text=src)
    return LayoutBraille()._indent_lines(bo, etype, 0)[1]


def test_항목_머리가_둘_이상이어도_첫_줄은_3칸():
    assert _indents([A, A, A], "다음 중 알맞은 것은?\n① 가\n② 나") == [2, 2, 2]


def test_항목_사이_이어지는_줄은_1칸():
    assert _indents([A, A, A, A], "다음 중 알맞은 것은?\n① 가\n이어지는 줄\n② 나") == [2, 2, 0, 2]


def test_상자_안_첫_줄도_3칸():
    got = _indents([TOP, A, A, A, BOT], "<!상자><!/상자>\n다음을 읽으시오.\n① 가\n② 나\n<!상자끝><!/상자끝>")
    assert got[1:4] == [2, 2, 2]


def test_캡션_첫_줄은_3칸():
    assert _indents([A, A], "가상의 그림 제목\n이어지는 줄", "caption") == [2, 0]


def test_번호와_갈린_코드_줄은_번호_줄이_머리다():
    at, lead = _q_blanks([A, A], "3\n[12345-0001] 다음 중 옳은 것은?")
    assert not at and lead                 # 번호와 코드 사이에 빈 줄 없음 · 요소 앞 빈 줄로 넘김


def test_요소_가운데서_갈리면_번호_줄_앞에_빈_줄():
    at, _lead = _q_blanks([A, A, A], "앞 문항 끝 줄\n3\n[12345-0001]")
    assert at == {1}


def test_코드로_여는_문항은_그대로_머리():
    """번호를 잃고 코드로 여는 문항 — gold 는 그 앞에 빈 줄을 둔다."""
    at, _lead = _q_blanks([A, A], "앞 문항 끝 줄\n[12345-0001]")
    assert at == {1}
    assert _is_q_head("[12345-0001]")
