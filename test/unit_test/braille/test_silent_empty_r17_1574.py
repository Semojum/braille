"""예외 없이 빈 점자를 내어 흔적 없이 사라지는 글자가 R17 미지 셈에 잡힌다(#1574). 예문은 지어낸 것이다."""
import pytest

from semojum_braille.encoder.translator import dropped_hanja, dropped_symbols, dropped_unknown


@pytest.mark.parametrize("text,ch", [
    ("café", "́"),      # NFD 로 온 양음 부호
    ("가̣나", "̣"),      # 아래 점
    ("x⃑", "⃑"),         # 위 오른쪽 작살표
])
def test_사라지는_결합_부호를_센다(text, ch):
    assert dropped_unknown(text)[ch] == 1


def test_다른_셈이_세는_글자는_겹쳐_세지_않는다():
    assert not dropped_unknown("가國나") and dropped_hanja("가國나")["國"] == 1
    assert not dropped_unknown("가⃞나") and dropped_symbols("가⃞나")["⃞"] == 1


def test_점형이_나오는_결합_부호는_안_센다():
    assert not dropped_unknown("가̅나")      # 윗줄은 점형이 있다
