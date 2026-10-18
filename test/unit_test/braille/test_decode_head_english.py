"""말머리·글머리 뒤 영어 몸통 역점역 — 줄 머리 토막을 한글로, 몸통을 영어 줄 판정으로 읽는다.

입력은 「한국 점자 규정」 예문 점자(재추출 행 번호)를 머리 + 몸통으로 이은 것이다. 머리는 제72항 글머리 기호
(□ `_7` 2886행 · • `_4` 2888행) · 제40항 수(1923행) + 제49항 마침표(2120행) · 제73항 [붙임] 예문 말머리 `일시:`
(2949~2950행)이고, 몸통은 영어 예문이다. 홀드아웃 권 줄은 쓰지 않는다(#1452). 규정 예문 점자는 백틱이 빈칸이다.
"""
import pytest

from braille_ascii import ascii_to_unicode
from semojum_braille.decoder.back import decode


def _br(s: str) -> str:
    return ascii_to_unicode(s, backtick="space")


_ARE = ">e`small`side`di%es`s}v$`al;g`)"      # 제39항 예문 둘째 줄(1904행)


@pytest.mark.parametrize("br, head, body", [
    ("``_4`" + _ARE, "  • ", "are small side dishes served along with"),
    ("``#a4`s}v$`al;g`)", "  1. ", "served along with"),                    # 같은 줄 끝 세 낱말
    # 제28항 [붙임] 예문(1494~1495행) 대문자 구절
    ("``#a4`,,,welcome`to`korea,'", "  1. ", "WELCOME TO KOREA"),
    # 쌍점으로 끝나는 한글 말머리 + 제33항 [다만] 예문(1689~1691행)의 로마자 구간
    ("``o1,o\"1`0,:at`,is`,a`,y|?8", "  일시: ", "What Is A Youth?"),
    ("``_7`" + _ARE, "  □ ", "are small side dishes served along with"),
])
def test_머리_뒤_영어(br, head, body):
    got = decode(_br(br))
    assert got.startswith(head) and got.endswith(body), got


def test_로마자_구간을_닫고_한글이_이어지면_자르지_않는다():
    # 단어장 꼴: 제37항 예문(1860~1862행)의 `help` 를 로마자 구간으로 닫고 같은 예문 `도움`(`ium5`)을 뜻으로 단다.
    # 영어 문단(제39항 예문 1903~1905행) 뒤에 두어 문맥 영어 판정을 받게 한다. 이 가드가 없으면 `□ help. iumen`.
    para = [_br(s) for s in ("``,ban*an`\"<,kor1n3`_(~3;<3_)\">", _ARE, "cook$`rice`9`,kor1n`cuis9e4")]
    assert decode("\n".join(para + [_br("``_7`0help4`ium5")])).split("\n")[-1] == "  □ help 도움"


def test_한글_낱말_머리는_자르지_않는다():
    # 비영어 책에서 몸통이 기능어 둘을 우연히 채우는 한국어 줄 — 머리 목록에 한글 낱말은 없다
    from semojum_braille.decoder import back as B
    assert not B._head_ok(_br("ium5"))             # 한글 낱말 `도움`(제37항 예문 1861행)
    assert not B._head_ok(_br(",'@[\"o5\"1"))      # 점역자주 표를 품은 말머리(「점자 자료 제작 지침」 예 6-1, 3029행)
