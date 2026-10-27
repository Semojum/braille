"""선택지 번호와 내용 사이에서는 줄을 나누지 않는다 — 「점자 자료 제작 지침」 4.2.4(3)(재추출 2399행).

번호(원문자 = ⠼ + 아래칸 숫자) 안 · 뒤 빈칸 · 내용 첫 셀 앞은 끊을 자리가 아니다. 정답 쌍의 답(`04 ③`)과 괄호 묶음이
가리키는 답(`(정답) ③ 풀이`)은 선택지 번호가 아니라 그대로 둔다. 글은 지어낸 것이다.
"""
import re

import pytest

from semojum_braille.encoder.translator import translate_with_breaks

_NUM = re.compile(r"⠼[⠂⠆⠒⠲⠢⠖⠶⠦⠔⠴]+⠀")


def _number_gaps(text: str) -> tuple[list[tuple[int, int]], set[int]]:
    """(번호 자리 (시작, 내용 시작) 목록, 끊을 자리)."""
    lines, breaks = translate_with_breaks(text)
    spans = [(m.start(), m.end()) for m in _NUM.finditer(lines[0]) if m.end() < len(lines[0])]
    return spans, set(breaks[0])


def test_선택지_번호_뒤에서는_끊지_않는다():
    spans, offs = _number_gaps("① 첫째 선택지의 내용이 꽤 길다 ② 둘째 선택지의 내용도 꽤 길다 ③ 셋째")
    assert len(spans) == 3
    for s, e in spans:
        assert not offs & set(range(s + 1, e + 1))     # 번호 안 · 뒤 빈칸 · 내용 첫 셀 앞
    assert {s for s, _ in spans[1:]} <= offs             # 번호 앞에서는 끊는다


@pytest.mark.parametrize("text", ["01 ③  02 ④", "(정답) ③ 풀이가 이어진다", "[답] ② 까닭은 이렇다"])
def test_답_번호는_그대로(text):
    spans, offs = _number_gaps(text)
    s, e = spans[0]
    assert e - 1 in offs or e in offs
