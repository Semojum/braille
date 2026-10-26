"""옹스트롬 기호 · ㎜Hg · 묵자 점형(#1570).

기대값은 「한국 점자 규정」 예문(재추출 행 번호)이거나 그 조항 꼴로 지은 문장이다. 교재 줄은 쓰지 않았다.
"""
import pytest

from semojum_braille.encoder.translator import translate_with_breaks


def _t(text: str) -> str:
    return "".join(translate_with_breaks(text)[0])


@pytest.mark.parametrize("text,want", [
    ("\u212b", "⠴⠡"),                                   # 제69항 [붙임 2] 2746행 `0*` — PDF 가 내는 옹스트롬 기호
    ("\u00c5", "⠴⠡"),
    ("파장은 5000 \u212b이다", "⠙⠨⠶⠵⠀⠼⠑⠚⠚⠚⠀⠴⠡⠀⠕⠊"),   # 비로마자 단위 뒤 한글 앞 한 칸(2739~2741행)
    ("1 \u212b은", "⠼⠁⠀⠴⠡⠀⠵"),                         # 숫자 뒤 단위는 수량이라 문항 번호 마침표가 안 붙는다
])
def test_옹스트롬은_단위표를_앞세운다(text, want):
    assert _t(text) == want


@pytest.mark.parametrize("text,want", [
    ("㎜Hg", "⠴⠍⠍⠠⠓⠛⠲"),                               # 과학 편 제30항 5035행 `0m m ,hg4`
    ("기압은 760 ㎜Hg 이다", "⠈⠕⠣⠃⠵⠀⠼⠛⠋⠚⠀⠴⠍⠍⠠⠓⠛⠲⠀⠕⠊"),
    ("160㎎/㎗를", "⠼⠁⠋⠚⠴⠍⠛⠸⠌⠙⠇⠲⠐⠮"),                  # 제69항 2691행 — 빗금 복합 단위는 종전 그대로
])
def test_사각_단위와_원소_기호는_한_구간이다(text, want):
    assert _t(text) == want


def test_사각_단위_뒤_소문자는_구간에_안_넣는다():
    assert "⠉⠍⠭" not in _t("10㎝x20㎝")


@pytest.mark.parametrize("text,want", [
    ("⠸⠹ 숫자 기호", "⠸⠿⠸⠹⠀⠠⠍⠄⠨⠀⠈⠕⠚⠥"),                     # 제67항 2646행
    ("마침표는 ⠲으로 적는다.", "⠑⠰⠕⠢⠙⠬⠉⠵⠀⠸⠿⠲⠀⠪⠐⠥⠀⠨⠹⠉⠵⠊⠲"),  # 2648행 — 뒤는 한 칸 띄운다
])
def test_묵자_점형은_점형표를_앞세운다(text, want):
    assert _t(text) == want


@pytest.mark.parametrize("text", ["◎ 가나다", "■ 가나"])
def test_엔진이_끼워_넣는_셀에는_점형표가_없다(text):
    assert "⠸⠿" not in _t(text)


def test_8점_셀에는_점형표가_없다():
    # 우리 점자는 6점이다. 엔진 사이드카가 쪽 번호 태그 자리표시(8점 `⣿…⣾`)를 점역에 흘려 보내므로 그대로 지나가야 한다
    assert "⠸⠿" not in _t("제⣿⣿⣿⣾쪽")
    assert "⣿⣿⣿⣾" in _t("제⣿⣿⣿⣾쪽")
