"""#1501 — 위 테두리에 안 드는 긴 제목은 잘리지 않고 테두리 윗줄 5칸에 간다.

「점자 자료 제작 지침」 2.1.7(4)②(재추출 580~581행): 위 테두리 제목은 7칸에 적고 앞뒤를 한 칸씩 띄되, 제목이 길어
위 테두리 안에서 26칸을 초과하면 위 테두리의 윗줄 5칸에 적는다(26칸 = 제목 + 뒤 빈칸 + 끝 캡 → 제목 자리 24칸).
기대 점자는 손으로 옮겼다: `구` = ㄱ ⠈ + ㅜ ⠍(약자 없음).
"""
from semojum_braille.encoder import translator as T
from semojum_braille.encoder.layout_braille import _box_blanks, _first_indented

TOP = "⠿" + "⠛" * 30 + "⠿"
BOTTOM = "⠿" + "⠶" * 30 + "⠿"


def test_긴_제목은_윗줄_5칸으로_자르지_않는다():
    lines, breaks = T.translate_with_breaks("<!상자>" + "구" * 13 + "<!/상자>\n본문")
    assert lines[0] == "⠀" * 4 + "⠈⠍" * 13          # 26칸 전부, 앞 빈칸 넷(5칸)
    assert lines[1] == TOP                              # 테두리는 제목 없이
    assert all(b > 4 for b in breaks[0])                # 끊을 자리도 제목 쪽으로 옮겨 간다
    assert T.box_borders_from_source("<!상자>" + "구" * 13 + "<!/상자>")[0] == ("top", 1, "")


def test_24칸_제목은_테두리_안_그대로():
    lines, _ = T.translate_with_breaks("<!상자>" + "구" * 12 + "<!/상자>\n본문")
    assert lines[0] == "⠿⠛⠛⠛⠛⠀" + "⠈⠍" * 12 + "⠀⠿"    # 캡 + 채움 4 + 빈칸 + 제목 24 + 빈칸 + 캡
    assert len(lines) == 2


def test_속글상자도_같다():
    lines, _ = T.translate_with_breaks("<!상자2>" + "구" * 13 + "<!/상자2>\n안쪽")
    assert lines[0] == "⠀" * 4 + "⠈⠍" * 13
    assert lines[1] == "⠖" + "⠒" * 30 + "⠲"


def test_조판은_윗줄_제목을_상자에_딸린_줄로_본다():
    title = "⠀" * 4 + "⠈⠍" * 13
    # 문단 들여쓰기는 제목이 아니라 테두리 안 첫 줄이 받는다
    assert _first_indented([title, TOP, "⠘⠷⠑⠛", BOTTOM]) == {2}
    # 앞 글과 상자 사이 빈 줄은 제목 줄 위에 온다(제목과 테두리 사이가 아니다)
    at, lead, tail = _box_blanks(["⠚⠽⠶", title, TOP, "⠘⠷⠑⠛", BOTTOM], off=False)
    assert 1 in at and 2 not in at and tail
    # 요소 첫 줄이 제목이면 요소 앞 빈 줄로 넘긴다
    at, lead, _ = _box_blanks([title, TOP, "⠘⠷⠑⠛", BOTTOM], off=False)
    assert lead and not at
