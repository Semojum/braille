"""AI #1424(원장 C-175) — 글상자 안 표는 위아래에 빈 줄을 두지 않는다. 상자 밖 표는 종전대로 한 줄씩 띈다.

AI 시험(`test_inner_table_blanks_1424.py`)은 AI 서버 배치 타입(`LayoutResult`)을 써서 못 옮긴다. 엔진 사이드카처럼
`flatten_elements` 에 배치 자리표시(`SimpleNamespace`)를 주어 같은 판정을 본다. 사이드카 `translate` 는 요소 앞뒤
빈 줄을 떼고 셀을 주므로, 이 빈 줄은 `flatten_elements` 를 바로 부르는 쪽(엔진 조판 1.7)에서 보인다.
"""
from types import SimpleNamespace
from uuid import uuid4

from semojum_braille.encoder.layout_braille import flatten_elements
from semojum_braille.encoder.table_braille import _TBL_BOT, _TBL_TOP, TableBraille
from semojum_braille.encoder.text_braille import TextBraille
from semojum_braille.schemas import LLMOutput

L2_TOP, L2_BOT = "⠖" + "⠒" * 30 + "⠲", "⠓" + "⠒" * 30 + "⠚"


def _lines(box_level: int) -> list[str]:
    ids = [uuid4() for _ in range(3)]
    texts = (("<!상자>보기<!/상자>\n상자 안 글이다.", "<!상자끝><!/상자끝>\n상자 밖 글이다.") if box_level
             else ("앞 글이다.", "뒤 글이다."))
    bos = TextBraille().translate([LLMOutput(element_id=i, corrected_text=t, render_mode="text_only", routing_tier="ZERO")
                                   for i, t in zip((ids[0], ids[2]), texts)])
    tb = TableBraille({ids[1]: box_level} if box_level else {}).translate(
        [LLMOutput(element_id=ids[1], corrected_text="구분|2000년\n초혼|88.9", render_mode="table_grid", routing_tier="ZERO")])[0]
    lr = SimpleNamespace(elements=[SimpleNamespace(element_id=i, type=t, reading_order=k, heading_level=0)
                                   for k, (i, t) in enumerate(zip(ids, ("text", "table", "text")))])
    flat = flatten_elements([bos[0], tb, bos[1]], lr)
    return "".join(flat[i].text for i in ids).split("\n")


def _around(lines: list[str], top: str, bot: str) -> tuple[str, str]:
    return lines[lines.index(top) - 1], lines[lines.index(bot) + 1]


def test_상자_안_표는_위아래_빈_줄이_없다(monkeypatch):
    monkeypatch.delenv("INNER_TABLE_BLANKS", raising=False)
    above, below = _around(_lines(1), L2_TOP, L2_BOT)
    assert above.strip("⠀ ") and below.startswith("⠿⠶")


def test_상자_밖_표와_끈_스위치는_종전대로_띈다(monkeypatch):
    monkeypatch.delenv("INNER_TABLE_BLANKS", raising=False)
    assert _around(_lines(0), _TBL_TOP, _TBL_BOT) == ("", "")
    monkeypatch.setenv("INNER_TABLE_BLANKS", "1")
    assert _around(_lines(1), L2_TOP, L2_BOT) == ("", "")
