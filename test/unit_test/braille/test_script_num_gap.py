"""숫자 첨자 뒤 숫자와 혼동되는 한글 띄움 — 「한글 점자」 제68항 [붙임 1]."""
from semojum_braille.encoder.translator import translate_with_breaks
from braille_ascii import ascii_to_unicode


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0])


def test_규정_예문():
    # 재추출 2656~2660행 `10,000㎡는 1㏊이다.` = ``#aj1jjj0m^#b`cz`#a0ha4oi4
    assert _tr("10,000㎡는 1㏊이다.") == ascii_to_unicode("#aj1jjj0m^#b`cz`#a0ha4oi4", backtick="space")


def test_헷갈리지_않는_한글은_붙인다():
    assert _tr("부피 2㎥를").endswith("⠘⠼⠉⠐⠮")
