"""면 끝 위 테두리 판정이 쓰는 꼴이 엔진 글상자 꼴(`encoder/constants.BOX_LEVELS`)과 어긋나지 않게 묶는다.
면 나눔 동작 자체는 `vectors.json` 의 '위 테두리' 케이스가 세 구현에서 본다."""
from semojum_braille.assist import _TOP_BORDERS, _is_top_border
from semojum_braille.encoder.constants import BOX_LEVELS


def test_위_테두리_꼴이_글상자_단계와_같다():
    assert set(_TOP_BORDERS) == {lv["top"] for lv in BOX_LEVELS.values()}


def test_아래_테두리는_위_테두리가_아니다():
    for lv in BOX_LEVELS.values():
        a, f, z = lv["bottom"]
        assert not _is_top_border(a + f * 30 + z, 32)
