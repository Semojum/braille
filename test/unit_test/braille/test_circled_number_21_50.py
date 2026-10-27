"""동그라미 숫자 21~50(㉑~㉟ · ㊱~㊿)이 점역에서 사라지지 않는다.

「한국 점자 규정」 제64항(재추출 2564~2565행): "동그라미 숫자는 수표 뒤에 숫자의 점형을 한 단 내려 적고" — 예 ① = #1.
기대 점자는 이 조문대로 손으로 옮겼다(2 = ⠆ · 1 = ⠂ · 3 = ⠒ · 5 = ⠢ · 6 = ⠖ · 0 = ⠴).
"""
import pytest

from semojum_braille.encoder.translator import translate_tagged_text


@pytest.mark.parametrize("text, cells", [
    ("㉑ 가", "⠼⠆⠂⠀⠫"),
    ("㉟ 가", "⠼⠒⠢⠀⠫"),
    ("㊱ 가", "⠼⠒⠖⠀⠫"),
    ("㊿ 가", "⠼⠢⠴⠀⠫"),
])
def test_동그라미_숫자_21_50(text, cells):
    assert translate_tagged_text(text) == cells
