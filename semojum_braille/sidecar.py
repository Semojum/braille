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
from semojum_braille.encoder.layout_braille import flatten_elements
from semojum_braille.encoder.text_braille import TextBraille
from semojum_braille.schemas import LLMOutput

_TB = TextBraille()
# 역점역은 영어책의 모호한 토막에서 낱말 판정을 처음 부를 때 판정기를 올린다(kiwi 면 약 2초).
# 그 판정을 반드시 부르는 실물 한 줄(`  1. universal / 셰익스피어`)로 기동 직후 뒤에서 한 번 불러 둔다.
_WARMUP = "⠀⠀⠼⠁⠲⠀⠴⠥⠝⠊⠧⠻⠎⠁⠇⠲⠀⠸⠌⠀⠠⠌⠕⠁⠠⠪⠙⠕⠎"


def translate(text: str, etype: str = "text", hlevel: int = 0) -> dict:
    """요소 하나 → `flatten_elements` 가 내는 요소 본문(앞뒤 빈 줄 뺀 것, 32칸으로 안 접음) + 줄을 바꿔도 되는 자리.

    `flatten_elements` 를 그대로 부르고 `prefix` · `suffix` 를 떼며, `breaks` 는 `prefix` 길이만큼 뺀다.
    따로 세지 않는다. 종전에는 줄 사이 구분자를 늘 한 칸으로 세어, 앞 줄이 ⠀ 로 끝나 구분자가 빈 문자열인 자리
    뒤로 끊을 자리가 하나씩 밀렸다(#30). AI 응답 `TextElement.breaks` 와 같은 함수(`_flat_breaks`)다.
    """
    bo = _TB._translate_one(LLMOutput(element_id=uuid.uuid4(), corrected_text=text, routing_tier="ZERO"))
    el = SimpleNamespace(element_id=bo.element_id, type=etype, reading_order=0, heading_level=hlevel)
    fe = flatten_elements([bo], SimpleNamespace(elements=[el])).get(bo.element_id)
    if fe is None:                       # 내용이 없는 요소는 flatten_elements 가 담지 않는다
        return {"cells": "", "breaks": []}
    n = len(fe.prefix)
    return {"cells": fe.text[n:len(fe.text) - len(fe.suffix)], "breaks": [b - n for b in fe.breaks]}


def grade(braille: str, source: str, etype: str = "text", ocr_confidence: float | None = None) -> dict:
    """요소 하나의 검수 등급과 왕복 일치도. AI 서버가 응답에 붙이는 `review_grade` · `round_trip` 과 같은 길이다
    (`confidence.annotate` 를 그대로 부른다 — 등급 기준이 그 길로 잰 실측에서 나왔다).

    ⚠ 등급은 **검수 순서**다. high 도 실측 정확도 89%라 '확인 불필요'가 아니라 '나중에 봐도 되는 것'이다.
    """
    el = {"id": 0, "type": etype, "contents": [braille], "ocr_confidence": ocr_confidence}
    confidence.annotate([el], {0: {"contents": [source]}}, decode)
    return {"grade": el["review_grade"], "round_trip": el.get("round_trip")}


def handle(req: dict) -> dict:
    op = req.get("op")
    if op == "translate":
        return translate(req.get("text", ""), req.get("type") or "text", int(req.get("heading_level") or 0))
    if op == "decode":
        return {"text": decode(req.get("braille", ""), english=bool(req.get("english")))}
    if op == "brf":
        return {"brf": build_brf_file(req.get("job") or {}).decode("ascii")}
    if op == "read_brf":
        return {"pages": parse_brf(req.get("brf", ""))}
    if op == "grade":
        return grade(req.get("braille", ""), req.get("source", ""), req.get("type") or "text",
                     req.get("ocr_confidence"))
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
