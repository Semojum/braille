"""네모 문자 안의 로마자 — 「한국 점자 규정」 제64항 예(재추출 2582 · 2584행) 네모 ㄱ = `_8=a0l` · 네모 a = `_80a0l`."""
from semojum_braille.encoder.translator import translate_with_breaks
from braille_ascii import ascii_to_unicode


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0])


def test_로마자는_로마자표를_앞세운다():
    assert _tr("<!네모글>a<!/네모글>") == ascii_to_unicode("_80a0l", backtick="space")


def test_한글은_그대로():
    assert _tr("<!네모글>ㄱ<!/네모글>") == ascii_to_unicode("_8=a0l", backtick="space")
