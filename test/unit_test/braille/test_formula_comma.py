"""식 뒤 쉼표는 식에 붙인다. 「수학 점자」 제12항 예 · 2027 gold.

종전에는 제11항 두 칸이 쉼표 앞에도 붙어 `f(x)  ,  g(x)` 꼴이 나갔다. 2027 gold(홀드아웃 뺌)에서
`$식$, $식$` 의 쉼표는 붙음 139 : 두 칸 0 이다.
"""
from semojum_braille.encoder.translator import translate_tagged_text
from braille_ascii import ascii_to_unicode


def test_규정_예문():
    # 제12항 예(재추출 3323~3325행) `두 연속함수 f(x),g(x)가 다음 조건을 만족시킨다.` = ``im`*,xj5,m``f8x0"`g8x0``$`i<[5 …
    out = translate_tagged_text("두 연속함수 $f(x)$, $g(x)$가 다음 조건을 만족시킨다.")
    assert ascii_to_unicode('``f8x0"`g8x0``$', backtick="space") in out


def test_묵자_쉼표_앞_빈칸도_같다():
    assert translate_tagged_text("두 함수 $f(x)$ , $g(x)$가") == translate_tagged_text("두 함수 $f(x)$, $g(x)$가")


def test_쉼표_뒤_한글은_한_칸():
    assert translate_tagged_text("$x=3$, 즉 해는").startswith("⠭⠒⠒⠼⠉⠐⠀⠨⠪⠁")


def test_식_뒤_쌍점도_붙인다():
    # 수학 제65항 1호 예(재추출 4270행) `#(A): A의 기수` = _?8,A0"1`0,A4W`@O,M — 쌍점이 닫는 괄호에 붙는다.
    out = translate_tagged_text("곡선 $y=x^{2}$: 원점을 지난다")
    assert "⠘⠼⠃⠐⠂⠀" in out and "⠀⠀⠐⠂" not in out
