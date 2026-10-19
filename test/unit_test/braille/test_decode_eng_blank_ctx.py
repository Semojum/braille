"""영어 역점역 — 빈칸 ⠨⠤ · 문맥 번짐 가드 · 점자 쪽 머리줄.

입력은 「한국 점자 규정」 · 「점자 도서 제작 지침」 예문 점자다(재추출 행 번호). 빈칸 시험만 예문 낱말 하나를
[부록 1] 영어 문장 부호 아래선(`_` 9408행 · `.-` 9415행)으로 바꿨다. 홀드아웃 권 줄은 쓰지 않는다(#1452).
규정 예문 점자는 백틱이 빈칸이다(`backtick="space"`).
"""
import re

import pytest

from semojum_braille.decoder import back as B
from braille_ascii import ascii_to_unicode
from semojum_braille.decoder.back import decode


def _br(s: str) -> str:
    return ascii_to_unicode(s, backtick="space")


# 제39항 예문(1901~1905행) `Banchan (Korean: 반찬) are small side dishes served along with cooked rice in Korean
# cuisine.` 세 줄. 문단 전체가 로마자라 로마자표가 없다(제29항 [다만] 1507행).
_PARA = [_br(s) for s in ("``,ban*an`\"<,kor1n3`_(~3;<3_)\">",
                          ">e`small`side`di%es`s}v$`al;g`)",
                          "cook$`rice`9`,kor1n`cuis9e4")]


@pytest.mark.parametrize("br, want", [
    # 제39항 예문 둘째 줄(1904행), 첫 명사구 자리에 빈칸 — 로마자표 없이 빈칸으로 시작하는 줄
    (".-`>e`small`side`di%es`s}v$`al;g`)", "___ are small side dishes served along with"),
    # 제33항 [다만] 예문(1689~1691행) `What Is A Youth?` 의 `Youth` 자리 — 로마자표로 연 줄, 문장 부호가 붙은 빈칸
    ("``0,:at`,is`,a`.-8", "  What Is A ___?"),
    # 제39항 예문(1896~1897행) `What is 김치 in English?` 의 한글 자리 — 줄 가운데 빈칸
    ("0,:at`is`.-`9`,5gli%8", "What is ___ in English?"),
])
def test_빈칸이_영어_줄을_막지_않는다(br, want):
    assert decode(_br(br)) == want


def test_문맥_번짐이_한국어_문장을_뒤집지_않는다(monkeypatch):
    # 제37항 [붙임] 예문(1868~1870행) 끝 낱말 `쓰시오.` 를 영어 문단 사이에 둔다
    page = "\n".join(_PARA[:2] + [_br(",,{,ou4")] + _PARA[2:])
    assert decode(page).split("\n")[2] == "쓰시오."
    monkeypatch.setattr(B, "_CTX_KIWI_GUARD", False)              # 가드가 없으면 `OWOU.`
    assert decode(page).split("\n")[2] == "OWOU."


def test_로마자표_머리줄은_문맥_영어가_안_된다(monkeypatch):
    # 「점자 도서 제작 지침」 [예 1-6] 페이지행(309행) 꼴: 원본 쪽 25 · 꼬리말 · 점자 쪽 21(수는 제40항 1923~1927행).
    # 꼬리말은 제29항 예문 `Table of Contents`(1505~1506행), 원본 쪽 앞 `a` 는 걸친 둘째 점자 쪽(같은 지침 315~316행).
    head = _br("a#be```````0,table`(`,3t5ts4``````#ba")
    page = "\n".join(_PARA + [head])
    assert decode(page).split("\n")[-1] == "a25       Table of Contents      21"
    monkeypatch.setattr(B, "_BRAILLE_PAGE_HEAD_RE", re.compile("(?!x)x"))  # 머리줄을 못 알아보면 종료표가 마침표가 된다
    assert decode(page).split("\n")[-1] == "a25       Table of Contents.      21"
