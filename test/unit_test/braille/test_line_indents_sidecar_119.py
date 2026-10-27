"""여러 줄 글의 둘째 줄부터 들여쓰기도 사이드카 `translate` 점자에 그대로 남는다(#119).

#97 은 빈칸을 점역 전에 `<!N칸>` 태그로 되돌렸다. 들여쓰기 판정(`_first_indent`)은 첫 줄 태그만 읽고, 둘째 줄부터의
태그는 번역기가 모르는 태그로 지워 그 줄들이 0칸이 됐다. 하향식 가계도 단계(「점자 자료 제작 지침」 6.6.4(2)② "후손
단계에 따라 하위 수준으로 갈수록 두 칸씩 들여쓰기") 같은 시각 골격이 앱 화면 · BRF 에서만 무너졌다. 글은 지어낸 것이다.
"""
import pytest

from semojum_braille.sidecar import handle

B = "⠀"
TREE = "1세대: 가 × 나\n  2세대: 다 × 라\n    3세대: 마"


def _pads(text: str, etype: str = "caption") -> list[int]:
    cells = handle({"op": "translate", "text": text, "type": etype})["cells"]
    return [len(x) - len(x.lstrip(B)) for x in cells.split("\n") if x.strip(B)]


@pytest.mark.parametrize("etype", ["caption", "diagram", "text"])
def test_둘째_줄부터_빈칸이_칸이_된다(etype):
    assert _pads(TREE, etype) == [0, 2, 4]


def test_빈칸_꼴이_태그_꼴과_같다():
    tagged = "1세대: 가 × 나\n<!2칸>2세대: 다 × 라\n<!4칸>3세대: 마"
    assert handle({"op": "translate", "text": tagged, "type": "caption"})["cells"] == \
        handle({"op": "translate", "text": TREE, "type": "caption"})["cells"]


def test_첫_줄만_들인_글은_종전과_같다():
    # 글 요소 첫 줄 3칸(앞빈칸 2), 둘째 줄은 0칸. 상자는 첫 칸을 테두리 안 첫 줄로 옮긴다.
    assert _pads("  첫 줄이다.\n둘째 줄이다.", "text") == [2, 0]
    box = _pads("  <!상자><!/상자>\n상자 글이다.\n<!상자끝><!/상자끝>", "text")
    assert box == [0, 2, 0]
