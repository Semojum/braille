"""줄머리 글머리 • 뒤는 한 칸이다(「한국 점자 규정」 제72항, 예 재추출 2904 · 2908행 `□ 2021 …` = `_7`#bjba…`).

추출이 • 뒤 칸을 잃어도(`•막대한`) 띄워 적는다. gold dev · val 줄머리 `_4` 뒤 빈칸 4,115 · 붙음 1. 예문은 지어낸 것이다.
"""
from __future__ import annotations

import pytest

from semojum_braille.encoder.translator import translate_with_breaks


def _t(text: str) -> str:
    return "\n".join(translate_with_breaks(text)[0])


@pytest.mark.parametrize("glued,spaced", [
    ("•가을 행사", "• 가을 행사"), ("•7월 행사", "• 7월 행사"), ("  •들여쓴 항목", "  • 들여쓴 항목"),
    ("첫 줄\n•둘째 줄", "첫 줄\n• 둘째 줄")])
def test_붙은_글머리도_한_칸(glued, spaced):
    assert _t(glued) == _t(spaced)
    assert "⠸⠲⠀" in _t(glued)


def test_글_중간_점은_그대로():
    assert "⠸⠲⠀" not in _t("정치•경제")


def test_제어_문자_틈은_한_칸만():
    # 추출이 칸 자리에 제어 문자를 남긴 꼴. 그 자리가 이미 빈칸이 된다
    assert "⠸⠲⠀⠀" not in _t("•\x07가을 행사")
