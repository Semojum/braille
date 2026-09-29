"""점역: 묵자를 한국어 점자로 옮긴다.

자주 쓰는 입구만 여기서 내보낸다. 나머지 공개 함수는 하위 모듈에서 부른다(docs/encoder.md).

    from semojum_braille.encoder import translate_tagged_text
    print(translate_tagged_text("대한민국의 모든 국민은 법 앞에 평등하다."))
"""
from semojum_braille.encoder.kor_math_rules import convert_latex
from semojum_braille.encoder.translator import (
    sanitize_for_braille,
    translate_body,
    translate_plain,
    translate_tagged_text,
    translate_visual,
    translate_with_breaks,
)

__all__ = [
    "convert_latex",
    "sanitize_for_braille",
    "translate_body",
    "translate_plain",
    "translate_tagged_text",
    "translate_visual",
    "translate_with_breaks",
]
