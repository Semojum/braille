"""핵형(상염색체 수 + 성염색체)은 식이다. 「과학 점자」 제23항 예 · 제6항.

`44+XX` 는 등호 · 그리스 문자 같은 수식 신호가 없어 글 경로로 샜다. 성염색체에 로마자표 · 종료표가 붙고
앞뒤가 한 칸이었다(`⠀⠼⠙⠙⠢⠴⠠⠠⠭⠭⠲⠕⠊⠲`). 규정 예는 식 앞뒤 두 칸 · 로마자표 없음이다.
"""
from semojum_braille.encoder.translator import translate_with_breaks


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0])


def test_규정_예문():
    # 제23항 예(재추출 4938~4940행) `정상 여자의 염색체는 44+XX이다.` = .]l7`:.<w`:5,ra;ncz``#dd5,,xx` / oi4.
    #   정본이 32칸에서 줄을 끊어 식 뒤 둘째 칸이 줄바꿈이 됐다(제6항 4423행 "식의 앞뒤를 두 칸씩").
    assert _tr("정상 여자의 염색체는 44+XX이다.").endswith("⠉⠵⠀⠀⠼⠙⠙⠢⠠⠠⠭⠭⠀⠀⠕⠊⠲")


def test_성염색체가_셋이어도_식이다():
    out = _tr("이 사람의 핵형은 44+XXY이다.")
    assert "⠴" not in out and "⠀⠀⠼⠙⠙⠢⠠⠠⠭⠭⠽⠀⠀" in out
