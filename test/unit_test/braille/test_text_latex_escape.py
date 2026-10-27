"""글 속 LaTeX 이스케이프(`\\$40` · `30\\%`)의 백슬래시가 역슬래시 점형(⠸⠡)으로 찍히던 자리."""
import pytest

from semojum_braille.encoder.translator import translate_with_breaks


def _tr(text: str) -> str:
    return "".join(translate_with_breaks(text)[0])


@pytest.mark.parametrize("escaped, plain", [
    ("① \\$40", "① $40"),          # 영어 듣기 금액 선택지 꼴 — 교열이 화폐 $ 를 수식 구분자와 가르려 붙인다
    ("비율은 30\\%이다", "비율은 30%이다"),
    ("A \\& B", "A & B"),
])
def test_이스케이프_백슬래시는_글자가_아니다(escaped, plain):
    out = _tr(escaped)
    assert "⠸⠡" not in out and out == _tr(plain)


def test_달러는_규정_꼴():
    # 「한글 점자」 제65항 예(재추출 2619~2620행) `$50` = 0@s#ej. 화폐 기호는 0 을 앞세운다.
    assert _tr("금액은 \\$50이다").endswith("⠴⠈⠎⠼⠑⠚⠕⠊")


def test_한_줄의_이스케이프_달러_둘은_수식_구분자가_아니다():
    # 영어 듣기 대본 꼴 `Admission is \$10 for adults, \$5 for teens.` — 두 `\$` 사이가 수식으로 짝지어져 깨졌다.
    out = _tr("Admission is \\$10 for adults, \\$5 for teens.")
    assert out.count("⠴⠈⠎") == 2 and "⠸⠡" not in out
