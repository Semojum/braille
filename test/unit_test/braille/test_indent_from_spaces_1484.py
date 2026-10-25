"""들여쓰기를 **실제 빈칸**으로 보내도 태그로 보낸 것과 같은 결과가 나온다(#1484).

#1482 로 응답 묵자가 들여쓰기를 태그 대신 실제 빈칸으로 싣게 됐다(대표 지시). 그 글이 돌아올 때
빈칸이 **두 번** 들어갔다 — 들여쓰기 판정이 값을 읽어 칸을 붙이는데 글자로 남은 빈칸도 같이 찍혔다.

    `  본문입니다`     → _first_indent 2 + 점자 앞빈칸 2 = 4   (지침 3칸이어야 하니 2)
    `      작은제목`   → _first_indent 2 + 점자 앞빈칸 2 = 4   (지침 7칸이어야 하니 6)

고침은 둘이다. `split_indent` 가 빈칸도 읽어 **떼어 내고**, `translate_body`(제품·채점기 공용
진입점)가 점역 전에 한 번 태그로 모은다. 엔진 `semojum_braille` 도 같다(braille #97 · v3.4.33).
"""
import uuid

import pytest

from semojum_braille.encoder.layout_braille import LayoutBraille
from semojum_braille.encoder.tag_names import split_indent, strip_indent_tags
from semojum_braille.encoder.text_braille import TextBraille
from semojum_braille.schemas import LLMOutput


def _total_indent(text: str) -> int:
    """들여쓰기 판정 + 점자에 찍힌 앞빈칸. 둘을 더한 것이 점역사가 보는 칸이다."""
    bo = TextBraille().translate(
        [LLMOutput(element_id=uuid.uuid4(), corrected_text=text, routing_tier="ZERO")])[0]
    cells = bo.braille_lines[0] if bo.braille_lines else ""
    lead = len(cells) - len(cells.lstrip("⠀"))
    return LayoutBraille()._first_indent(bo, "text", False, 0) + lead


@pytest.mark.parametrize("tagged,spaced", [
    ("<!2칸>본문입니다", "  본문입니다"),
    ("<!4칸>제목입니다", "    제목입니다"),
    ("<!6칸>작은제목", "      작은제목"),
])
def test_빈칸_꼴이_태그_꼴과_같다(tagged, spaced):
    assert _total_indent(tagged) == _total_indent(spaced)


@pytest.mark.parametrize("spaced,want", [("  가", 2), ("    가", 4), ("      가", 6)])
def test_빈칸_수가_그대로_칸이_된다(spaced, want):
    assert _total_indent(spaced) == want


def test_들여쓰기가_없으면_유형_기본값이다():
    """글 요소는 문단 3칸(앞빈칸 2)에서 시작한다 — 종전 동작."""
    assert _total_indent("본문입니다") == 2


class TestSplitIndent:
    def test_태그를_읽는다(self):
        assert split_indent("<!4칸>가나다") == (4, "가나다")

    def test_빈칸을_읽고_떼어_낸다(self):
        """떼지 않으면 글자로 남아 두 번 들어간다."""
        assert split_indent("    가나다") == (4, "가나다")

    def test_들여쓰기가_없으면_None(self):
        assert split_indent("가나다") == (None, "가나다")

    def test_빈_줄은_들여쓰기가_아니다(self):
        assert split_indent("   ") == (None, "   ")

    def test_여러_줄도_같이_읽는다(self):
        body, inds = strip_indent_tags("제목\n  본문\n    깊은 줄")
        assert body == "제목\n본문\n깊은 줄" and inds == [0, 2, 4]
