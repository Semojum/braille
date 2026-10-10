"""점역·역점역 사이드카. 파이썬이 아닌 프로그램이 이 프로세스를 띄우고 표준입출력으로 한 줄짜리 JSON 을 주고받는다.

    python -m semojum_braille.sidecar

요청 한 줄에 응답 한 줄이다. 받은 순서대로 답한다. 표준출력에는 응답만 쓰고, 로그는 표준오류로 간다.
표준입력이 닫히면 끝난다. 프로토콜은 docs/sidecar.md.
"""
import json
import sys
import threading
import uuid
from types import SimpleNamespace

from semojum_braille import confidence
from semojum_braille.assist import build_brf_file
from semojum_braille.brf import parse_brf
from semojum_braille.decoder import decode
from semojum_braille.encoder import inline_math
from semojum_braille.encoder.constants import ENGLISH_GRADE1, KOREAN_GRADE1
from semojum_braille.encoder.layout_braille import flatten_elements
from semojum_braille.encoder.text_braille import TextBraille
from semojum_braille.encoder.translator import dropped_old_jamo, dropped_pua, dropped_symbols
from semojum_braille.schemas import LLMOutput

_TB = TextBraille()
# 역점역은 영어책의 모호한 토막에서 낱말 판정을 처음 부를 때 판정기를 올린다(kiwi 면 약 2초).
# 그 판정을 반드시 부르는 실물 한 줄(`  1. universal / 셰익스피어`)로 기동 직후 뒤에서 한 번 불러 둔다.
_WARMUP = "⠀⠀⠼⠁⠲⠀⠴⠥⠝⠊⠧⠻⠎⠁⠇⠲⠀⠸⠌⠀⠠⠌⠕⠁⠠⠪⠙⠕⠎"
# 점자 기호가 없어 조용히 빠지는 글자. AI 서버가 쪽 플래그(R15 PUA · R17 기호 · R18 옛한글)를 세는 함수 그대로다.
_DROPPED = (("R15", dropped_pua), ("R17", dropped_symbols), ("R18", dropped_old_jamo))


def translate(text: str, etype: str = "text", hlevel: int = 0,
              korean_grade1: bool = False, english_grade1: bool = False, math_page: bool = False) -> dict:
    """요소 하나 → `flatten_elements` 가 내는 요소 본문(앞뒤 빈 줄 뺀 것, 32칸으로 안 접음) + 줄을 바꿔도 되는 자리
    + 점자에서 빠진 글자.

    `flatten_elements` 를 그대로 부르고 `prefix` · `suffix` 를 떼며, `breaks` 는 `prefix` 길이만큼 뺀다.
    따로 세지 않는다. 종전에는 줄 사이 구분자를 늘 한 칸으로 세어, 앞 줄이 ⠀ 로 끝나 구분자가 빈 문자열인 자리
    뒤로 끊을 자리가 하나씩 밀렸다(#30). AI 응답 `TextElement.breaks` 와 같은 함수(`_flat_breaks`)다.

    `korean_grade1` · `english_grade1` 은 한글 정자 · 영어 1급이다(AI proto 의 같은 이름 필드). 엔진 문맥 값을
    이 호출 동안만 켠다. 사이드카는 오래 사는 프로세스라 켠 값이 다음 요청으로 새면 안 된다(#34).

    `math_page` 는 그 요소가 든 쪽이 수식 쪽이라는 뜻이다(`inline_math.MATH_PAGE`, #38). AI 서버는 쪽 PDF 의 한컴
    수식 글꼴 비율로 정하고, 수식 쪽이면 평문 속 `(1, 0)` · `p-q` 를 수식으로 적는다. 앱에서 수식 쪽 글을 다시
    점역할 때 넘겨야 서버가 낸 점자와 같다.
    """
    tokens = KOREAN_GRADE1.set(korean_grade1), ENGLISH_GRADE1.set(english_grade1), inline_math.MATH_PAGE.set(math_page)
    try:
        bo = _TB._translate_one(LLMOutput(element_id=uuid.uuid4(), corrected_text=text, routing_tier="ZERO"))
        el = SimpleNamespace(element_id=bo.element_id, type=etype, reading_order=0, heading_level=hlevel)
        fe = flatten_elements([bo], SimpleNamespace(elements=[el])).get(bo.element_id)
    finally:
        KOREAN_GRADE1.reset(tokens[0])
        ENGLISH_GRADE1.reset(tokens[1])
        inline_math.MATH_PAGE.reset(tokens[2])
    dropped = [{"text": t, "count": n, "flag": flag} for flag, count in _DROPPED for t, n in count(text).most_common()]
    if fe is None:                       # 내용이 없는 요소는 flatten_elements 가 담지 않는다
        return {"cells": "", "breaks": [], "dropped": dropped}
    n = len(fe.prefix)
    return {"cells": fe.text[n:len(fe.text) - len(fe.suffix)], "breaks": [b - n for b in fe.breaks], "dropped": dropped}


def _flag(req: dict, key: str) -> bool:
    """참거짓 옵션. 없거나 null 이면 false. 문자열 "true" 같은 값은 조용히 켜거나 끄지 않고 오류로 돌려준다."""
    v = req.get(key)
    if v is None or isinstance(v, bool):
        return bool(v)
    raise ValueError(f"{key} 는 true · false 여야 한다: {v!r}")


def grade(braille: str, source: str, etype: str = "text", ocr_confidence: float | None = None,
          korean_grade1: bool = False) -> dict:
    """요소 하나의 검수 등급과 왕복 일치도. AI 서버가 응답에 붙이는 `review_grade` · `round_trip` 과 같은 길이다
    (`confidence.annotate` 를 그대로 부른다 — 등급 기준이 그 길로 잰 실측에서 나왔다).

    `korean_grade1` 은 `braille` 이 한글 정자로 점역된 것이라는 뜻이다. 왕복 일치도를 잴 때 역점역이 정자로 읽는다.
    2급 역맵으로 읽으면 정자 문서의 등급이 거의 다 low 가 된다(AI #1276).

    ⚠ 등급은 **검수 순서**다. high 도 실측 정확도 89%라 '확인 불필요'가 아니라 '나중에 봐도 되는 것'이다.
    """
    el = {"id": 0, "type": etype, "contents": [braille], "ocr_confidence": ocr_confidence}
    confidence.annotate([el], {0: {"contents": [source]}}, lambda b: decode(b, korean_grade1=korean_grade1))
    return {"grade": el["review_grade"], "round_trip": el.get("round_trip")}


def handle(req: dict) -> dict:
    op = req.get("op")
    if op == "translate":
        return translate(req.get("text", ""), req.get("type") or "text", int(req.get("heading_level") or 0),
                         _flag(req, "korean_grade1"), _flag(req, "english_grade1"), _flag(req, "math_page"))
    if op == "decode":
        return {"text": decode(req.get("braille", ""), english=bool(req.get("english")),
                               korean_grade1=_flag(req, "korean_grade1"))}
    if op == "brf":
        return {"brf": build_brf_file(req.get("job") or {}).decode("ascii")}
    if op == "read_brf":
        return {"pages": parse_brf(req.get("brf", ""))}
    if op == "grade":
        return grade(req.get("braille", ""), req.get("source", ""), req.get("type") or "text",
                     req.get("ocr_confidence"), _flag(req, "korean_grade1"))
    if op == "ping":
        return {"ok": True}
    return {"error": f"모르는 op: {op!r}"}


def main() -> None:
    threading.Thread(target=decode, args=(_WARMUP,), kwargs={"english": True}, daemon=True).start()
    for raw in sys.stdin:
        if not raw.strip():
            continue
        req = {}
        try:
            req = json.loads(raw)
            res = handle(req)
        except Exception as exc:          # 한 요청이 실패해도 사이드카는 산다
            res = {"error": f"{type(exc).__name__}: {exc}"}
        res["id"] = req.get("id") if isinstance(req, dict) else None
        sys.stdout.write(json.dumps(res, ensure_ascii=True) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
