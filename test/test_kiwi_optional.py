"""kiwipiepy 는 선택 의존이다(`pip install semojum-braille[kiwi]`). 있을 때와 없을 때를 둘 다 본다.

없으면 역점역의 한국어 낱말 판정이 낱말 목록(`decoder/kor_words.json`)으로 간다. 그 차이를
영어 교과 책의 실물 줄 셋으로 고정한다(점자 코퍼스 EBS-E26-008 · HS-REF-007 · EBS-E26-006).
kiwi 가 없는 환경은 `kiwipiepy` 임포트를 막아 만든다(깔리지 않은 것과 같은 ImportError).
"""
from __future__ import annotations

import sys

import pytest

from semojum_braille.decoder import back, decode, wordlist

YOUR = "⠀⠀⠰⠠⠍⠒⠀⠠⠞⠄⠎⠀⠝⠕⠗⠍⠁⠇⠲⠀⠠⠽⠗⠀⠃⠕⠙⠽"          # 영어 Your 를 kiwi 가 한국어 `쇠애` 로 본다
SSEOYA = "⠴⠞⠕⠲⠀⠘⠍⠨⠻⠇⠐⠮⠀⠠⠠⠎⠜⠀⠚⠑⠪⠐⠥⠀⠦⠴⠡⠕⠕⠎⠑⠴"   # 한국어 `써야` 는 목록도 안다
SHAKESPEARE = "⠀⠀⠼⠁⠲⠀⠴⠥⠝⠊⠧⠻⠎⠁⠇⠲⠀⠸⠌⠀⠠⠌⠕⠁⠠⠪⠙⠕⠎"     # `셰익스피어` 는 목록이 모른다


@pytest.fixture
def no_kiwi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "kiwipiepy", None)    # import kiwipiepy → ImportError
    monkeypatch.setattr(back, "_KIWI", None)               # 판정기를 다시 고르게 한다


def test_목록_판정_규칙() -> None:
    assert wordlist.known(["써야"])
    assert not wordlist.known(["써야", "쇠애"])              # 덩어리가 모두 목록에 있어야 한다
    assert not wordlist.known([])                           # 한글 덩어리가 없으면 낱말이 아니다
    assert not wordlist.known(["숙"])                       # 한 음절 홀로는 낱말로 보지 않는다
    assert not wordlist.known(["쇠애"])                     # 영어를 한글로 잘못 읽은 조각
    assert len(wordlist.words()) == 27_790


def test_kiwi_없으면_목록으로_가른다(no_kiwi: None) -> None:
    assert back._is_real_korean("써야")
    assert not back._is_real_korean("쇠애")
    assert not back._is_real_korean("a써야")                # 라틴이 끼면 낱말이 아니다(원본 함수 앞머리)
    assert back._KIWI is False                              # 없다는 것을 기억해 매번 임포트하지 않는다


def test_kiwi_없을_때_실물_줄(no_kiwi: None) -> None:
    assert decode(YOUR, english=True) == "  M= 섨어 에이애욱사. Your b이푀"
    assert decode(SSEOYA, english=True) == "to 부정사를 써야 하므로 \"choose”"
    assert decode(SHAKESPEARE, english=True) == "  1. universal / StoaOwdos"


def test_kiwi_있을_때_실물_줄() -> None:
    pytest.importorskip("kiwipiepy")
    assert decode(YOUR, english=True) == "  M= 섨어 에이애욱사. 쇠애 b이푀"
    assert decode(SSEOYA, english=True) == "to 부정사를 써야 하므로 \"choose”"
    assert decode(SHAKESPEARE, english=True) == "  1. universal / 셰익스피어"


def test_kiwi_없어도_한글만_있는_점자는_같다(no_kiwi: None) -> None:
    assert decode("⠊⠗⠚⠒⠑⠟⠈⠍⠁") == "대한민국"
