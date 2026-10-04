"""점역·역점역 사이드카. 파이썬이 아닌 프로그램이 이 프로세스를 띄우고 표준입출력으로 한 줄짜리 JSON 을 주고받는다.

    python -m semojum_braille.sidecar

요청 한 줄에 응답 한 줄이다. 받은 순서대로 답한다. 표준출력에는 응답만 쓰고, 로그는 표준오류로 간다.
표준입력이 닫히면 끝난다. 프로토콜은 docs/sidecar.md.
"""
import json
import sys
import threading
import uuid

from semojum_braille.assist import build_brf_file
from semojum_braille.decoder import decode
from semojum_braille.encoder.layout_braille import LayoutBraille, _fold_full_lines, _pad_join
from semojum_braille.encoder.text_braille import TextBraille
from semojum_braille.schemas import LLMOutput

_TB, _LB = TextBraille(), LayoutBraille()
# 역점역은 영어책의 모호한 토막에서 낱말 판정을 처음 부를 때 판정기를 올린다(kiwi 면 약 2초).
# 그 판정을 반드시 부르는 실물 한 줄(`  1. universal / 셰익스피어`)로 기동 직후 뒤에서 한 번 불러 둔다.
_WARMUP = "⠀⠀⠼⠁⠲⠀⠴⠥⠝⠊⠧⠻⠎⠁⠇⠲⠀⠸⠌⠀⠠⠌⠕⠁⠠⠪⠙⠕⠎"


def translate(text: str, etype: str = "text", hlevel: int = 0) -> dict:
    """요소 하나 → `flatten_elements` 가 내는 요소 본문(앞뒤 빈 줄 뺀 것)과 같은 통 문자열(32칸으로 안 접음) + 줄을 바꿔도 되는 자리.

    `flatten_elements` 가 요소 본문을 만드는 순서 그대로 부른다(들여쓰기 → 꽉 찬 줄 잇기 → 잇기).
    줄별 음절 경계를 들여쓰기 칸과 앞 줄 길이만큼 밀어 통 문자열 오프셋으로 옮긴다.
    """
    bo = _TB._translate_one(LLMOutput(element_id=uuid.uuid4(), corrected_text=text, routing_tier="ZERO"))
    lines, pads = _LB._indent_lines(bo, etype, hlevel)
    pads, seps = _fold_full_lines(lines, pads, etype, text.split("\n"))
    breaks, base = [], 0
    for i, (ln, pad) in enumerate(zip(lines, pads)):
        breaks += [base + pad + b for b in (bo.break_points[i] if i < len(bo.break_points) else [])]
        base += pad + len(ln) + 1
        if i < len(seps) and seps[i] != "\n":     # 꽉 찬 줄을 빈칸으로 이은 자리도 끊을 수 있다
            breaks.append(base - 1)
    return {"cells": _pad_join(lines, pads, seps), "breaks": breaks}


def handle(req: dict) -> dict:
    op = req.get("op")
    if op == "translate":
        return translate(req.get("text", ""), req.get("type") or "text", int(req.get("heading_level") or 0))
    if op == "decode":
        return {"text": decode(req.get("braille", ""), english=bool(req.get("english")))}
    if op == "brf":
        return {"brf": build_brf_file(req.get("job") or {}).decode("ascii")}
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
