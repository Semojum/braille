"""들여쓰기를 **실제 빈칸**으로 보내도 태그로 보낸 것과 같은 점자가 나온다(2026-10-22 대표 지시).

AI 응답의 묵자는 이제 들여쓰기를 태그(`<!2칸>`)가 아니라 실제 빈칸으로 싣는다. 점역사 화면에
기계 표식을 안 보이려는 것이다. 그 글이 앱을 거쳐 이 엔진으로 돌아온다.

종전에는 빈칸이 **두 번** 들어갔다. 들여쓰기 판정(`layout_braille._first_indent`)이 요소 유형만
보고 기본값을 매기는데, 글자로 남은 빈칸도 같이 찍혔다. 제품 경로(사이드카 `translate` op) 실측:

    지침 3칸 본문 → 앞빈칸 4   (기본 2 + 글자 2)
    지침 7칸 제목 → 앞빈칸 4   (유형 기본값으로 떨어짐)

고침은 둘이다. `split_indent` 가 빈칸도 읽어 **떼어 내고**, 사이드카 `translate` 가 점역 전에
한 번 태그로 모은다. 그래서 하류는 종전 경로를 그대로 탄다.
"""
import pytest

from semojum_braille.encoder.tag_names import split_indent, strip_indent_tags
from semojum_braille.sidecar import handle


def _pad(text: str) -> int:
    cells = handle({"op": "translate", "text": text, "type": "text"}).get("cells", "")
    return len(cells) - len(cells.lstrip("⠀"))


@pytest.mark.parametrize("tagged,spaced", [
    ("<!2칸>본문입니다", "  본문입니다"),
    ("<!4칸>제목입니다", "    제목입니다"),
    ("<!6칸>작은제목", "      작은제목"),
])
def test_빈칸_꼴이_태그_꼴과_같은_점자를_낸다(tagged, spaced):
    a = handle({"op": "translate", "text": tagged, "type": "text"})
    b = handle({"op": "translate", "text": spaced, "type": "text"})
    assert a["cells"] == b["cells"], (tagged, spaced)


@pytest.mark.parametrize("spaced,want", [("  가", 2), ("    가", 4), ("      가", 6)])
def test_빈칸_수가_그대로_칸이_된다(spaced, want):
    assert _pad(spaced) == want


def test_들여쓰기가_없으면_유형_기본값이다():
    """글 요소는 문단 3칸(앞빈칸 2)에서 시작한다 — 종전 동작."""
    assert _pad("본문입니다") == 2


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
