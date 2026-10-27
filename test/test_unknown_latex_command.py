"""모르는 수식 명령이 엔진에서 흔적 없이 사라지지 않는다(AI #1619 의 엔진 쪽 짝).

AI 시험 `test_latex_command_dropped_1618.py` 는 R17 검토 표시를 AI 서버 `app.core.pipeline` 에서 확인해
엔진으로 옮기지 못한다(`tools/tests_from_ai.txt`). 같은 뜻을 엔진 모듈과 앱이 부르는 사이드카 길로 본다.
기대 점형은 「한국 점자 규정」 수학 점자 예문(재추출 3711~3714행 · 3778행 · 4279행)이고, 그 밖의 예문은 지어낸 것이다.
"""
from semojum_braille import sidecar
from semojum_braille.encoder.kor_math_rules import convert_latex
from semojum_braille.encoder.translator import dropped_latex


def _cells(text: str) -> str:
    return sidecar.handle({"op": "translate", "text": text, "type": "text"})["cells"].strip("⠀")


def test_정규부분군_세모꼴은_사이드카에서도_앞뒤_한_칸():
    assert _cells("<!수식>G \\triangleright N<!/수식>") == "⠠⠛⠀⠸⠜⠀⠠⠝"      # ,g _> ,n
    assert _cells("<!수식>N \\triangleleft G<!/수식>") == "⠠⠝⠀⠸⠣⠀⠠⠛"       # ,n _< ,g


def test_닮음과_알레프가_사라지지_않는다():
    assert "⠠⠄" in convert_latex(r"\triangle ABC \backsim \triangle DEF")
    assert "⠗⠋" in convert_latex(r"c = 2^{\aleph_0}")


def test_모르는_명령은_세고_서식_명령은_안_센다():
    assert dropped_latex("<!수식>x \\vert y \\bigcirc<!/수식>") == {"\\vert": 1, "\\bigcirc": 1}
    assert dropped_latex("두 원 $A \\bigcirc B$ 가 있다") == {"\\bigcirc": 1}
    assert not dropped_latex("<!수식>G \\triangleright N<!/수식>")          # 점형이 있다
    assert not dropped_latex("가나다 ABC 123")
