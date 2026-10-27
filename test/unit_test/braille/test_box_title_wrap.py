"""상자 위 테두리 윗줄 제목이 넘치면 이어지는 줄도 첫 줄 시작 칸(5칸)에 맞춘다.

「점자 자료 제작 지침」 2.1.7(1)①(재추출 578행). 제목은 지어낸 것이다.
"""
from semojum_braille.encoder.translator import translate_tagged_text, translate_with_breaks

_TITLE = "아주 긴 상자 제목이 위 테두리 안에서 스물여섯 칸을 넘는다"


def test_긴_상자_제목은_이어지는_줄도_5칸에서_시작한다():
    lines, breaks = translate_with_breaks(f"<!상자>{_TITLE}<!/상자>\n상자 안 글\n<!상자끝><!/상자끝>")
    head = lines[:next(i for i, x in enumerate(lines) if x.startswith("⠿"))]
    assert len(head) == 2
    assert all(x.startswith("⠀" * 4) and x[4] != "⠀" and len(x) <= 32 for x in head)
    assert "".join(x[4:] for x in head).replace("⠀", "") == translate_tagged_text(_TITLE).replace("⠀", "")
    assert all(4 < b < len(x) for x, bs in zip(head, breaks) for b in bs)


def test_짧은_상자_제목은_테두리_안():
    lines, _ = translate_with_breaks("<!상자>짧은 제목<!/상자>\n상자 안 글\n<!상자끝><!/상자끝>")
    assert lines[0].startswith("⠿") and translate_tagged_text("짧은 제목") in lines[0]
