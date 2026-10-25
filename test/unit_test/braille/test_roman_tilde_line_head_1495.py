"""#1495 — 줄머리 · 부호 뒤 로마자 범위(`A~C`)도 구간 하나다. 로마자 뒤 물결표 + 한글은 종료표를 적는다."""
import pytest

from semojum_braille.encoder import translator as T


@pytest.mark.parametrize("src", [
    "A~C 중 하나를 고른다",
    "(나) A~D에 물을 붓는다",
    "교사: A~C 중에서 고르세요",
    "• A~C 중 하나는",
])
def test_줄머리와_부호_뒤_로마자_범위도_구간_하나(src):
    # 「한국 점자 규정」(재추출) 제29항 1496~1498행: 연이은 로마자는 첫 로마자 앞 로마자표 하나 · 마지막 뒤 종료표.
    #   제32항 1650행: 그 사이는 통일영어점자. 문장 가운데 꼴(#1329 `시험관 A~F에`)과 같아야 한다.
    #   90권 gold(홀드아웃 뺌) 한 구간 꼴 439회 · 다시 연 꼴 0회.
    out = T.translate_tagged_text(src)
    assert "⠴⠠⠁⠈⠔⠠" in out
    assert "⠈⠔⠴" not in out


def test_로마_숫자_범위도_구간_하나():
    assert "⠴⠠⠊⠈⠔⠠⠠⠊⠊⠊⠲" in T.translate_tagged_text("• Ⅰ~Ⅲ 중 하나는")


def test_로마자_뒤_물결표_한글은_종료표():
    # 제33항 [다만] 1682~1684행: ‘/ - ~’는 문장 부호 앞에 로마자 종료표를 적는다. 대문자로 시작하지 않아도 같다.
    assert "⠽⠲⠈⠔" in T.translate_tagged_text("summary~연습")


def test_한글_없는_줄은_그대로():
    assert "⠴" not in T.translate_tagged_text("A~B~C")
