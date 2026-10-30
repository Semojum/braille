# -*- coding: utf-8 -*-
"""머리말 정렬(`header_align`). 2026-10-31 신설.

종전에는 머리말이 가운데로 고정이었다. 앱의 「머리말 좌·우 정렬」이 비활성이던 까닭이
엔진에 이 옵션이 없어서였다(QA 4차 · server-work-required 10절).
꼬리말과 달리 머리말은 면 첫 줄을 통째로 쓰므로 좌우에 번호가 없다.
"""
import pytest

from semojum_braille.assist import Options, _header_line

COLS = 32
TEXT = "⠈⠅⠑"          # 점자 세 칸


@pytest.mark.parametrize("align, 앞_빈칸", [("left", 0), ("center", 15), ("right", 29)])
def test_정렬마다_앞_빈칸이_다르다(align, 앞_빈칸):
    line = _header_line(TEXT, 1, "", COLS, align)
    assert len(line) - len(line.lstrip("⠀")) == 앞_빈칸
    assert line.endswith(TEXT)


def test_기본값은_가운데라_옛_동작이_그대로다():
    assert _header_line(TEXT, 1, "", COLS) == _header_line(TEXT, 1, "", COLS, "center")


def test_오른쪽은_마지막_칸에_붙는다():
    assert len(_header_line(TEXT, 1, "", COLS, "right")) == COLS


def test_빈_머리말은_빈_줄이다():
    assert _header_line("", 1, "", COLS, "left") == ""


def test_모르는_값은_거부한다():
    with pytest.raises(ValueError, match="header_align"):
        Options(header_align="middle")


def test_옵션_기본값이_가운데다():
    assert Options().header_align == "center"
