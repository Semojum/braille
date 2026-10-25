"""#1496 — 줄여 쓴 연도 `’88` 은 수표 · 아포스트로피 · 숫자(⠼⠄⠓⠓). 닫는 작은따옴표 ⠴⠄ 가 아니다."""
import pytest

from semojum_braille.encoder import translator as T


@pytest.mark.parametrize("src,want", [
    # 「한국 점자 규정」(재추출) 제61항 2547행 · 예문 2549~2552행(정본 BRF 를 손으로 옮김)
    ("’22. 9. 7.", "⠼⠄⠃⠃⠲⠀⠼⠊⠲⠀⠼⠛⠲"),            # #'bb4`#i4`#g4
    ("’88 서울 올림픽", "⠼⠄⠓⠓⠀⠠⠎⠯⠀⠥⠂⠐⠕⠢⠙⠕⠁"),    # #'hh`,s&`u1"o5doa
])
def test_규정_예문(src, want):
    assert T.translate_tagged_text(src) == want


def test_곧은_따옴표와_범위도_같다():
    assert T.translate_tagged_text("'88 서울").startswith("⠼⠄⠓⠓")
    assert "⠼⠄⠓⠃⠈⠔⠼⠄⠃⠉" in T.translate_tagged_text("’82~’23 시기")


def test_글_경로도_물결_뒤_범위_끝까지():
    # 글 경로는 #939 가 낱말 머리 ’82 만 바꾸고 물결 뒤 ’23 은 ⠴⠄⠼ 로 남겼다.
    lines, _ = T.translate_with_breaks("’82~’23 시기")
    assert "⠼⠄⠓⠃⠈⠔⠼⠄⠃⠉" in lines[0]


def test_따옴표와_받침_ㅅ은_그대로():
    assert "⠴⠄⠼⠉" in T.translate_tagged_text("‘가’3")      # 앞이 글자면 닫는 작은따옴표
    assert T.translate_tagged_text("낫3").startswith("⠉⠄⠼⠉")   # 받침 ㅅ + 수
    # 곧은 따옴표로 시각을 감싼 글(dev · val 캡션에 실제로 있는 꼴)은 따옴표다
    assert "⠼⠄" not in T.translate_tagged_text("화면에 '12:34 / 56:07'가 보인다")
