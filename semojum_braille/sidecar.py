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

from semojum_braille import __version__, confidence
from semojum_braille.assist import build_brf_file
from semojum_braille.brf import parse_brf
from semojum_braille.decoder import decode
from semojum_braille.encoder import inline_math
from semojum_braille.encoder.constants import ENGLISH_GRADE1, KOREAN_GRADE1
from semojum_braille.encoder.isolation import is_blocked_braille, safe_translate
from semojum_braille.encoder.layout_braille import flatten_elements
from semojum_braille.encoder.table_braille import TableBraille
from semojum_braille.encoder.tag_names import parse_table_tags
from semojum_braille.encoder.text_braille import TextBraille
from semojum_braille.encoder.translator import dropped_old_jamo, dropped_pua, dropped_symbols, translate_with_breaks
from semojum_braille.schemas import LLMOutput

_TB = TextBraille()
# 역점역은 영어책의 모호한 토막에서 낱말 판정을 처음 부를 때 판정기를 올린다(kiwi 면 약 2초).
# 그 판정을 반드시 부르는 실물 한 줄(`  1. universal / 셰익스피어`)로 기동 직후 뒤에서 한 번 불러 둔다.
_WARMUP = "⠀⠀⠼⠁⠲⠀⠴⠥⠝⠊⠧⠻⠎⠁⠇⠲⠀⠸⠌⠀⠠⠌⠕⠁⠠⠪⠙⠕⠎"
# 점자 기호가 없어 조용히 빠지는 글자. AI 서버가 쪽 플래그(R15 PUA · R17 기호 · R18 옛한글)를 세는 함수 그대로다.
_DROPPED = (("R15", dropped_pua), ("R17", dropped_symbols), ("R18", dropped_old_jamo))
# 프로토콜 판. 요청 · 응답 꼴이 앞 판과 호환되지 않게 바뀔 때만 올린다. 필드 · op 를 더하는 것은 올리지 않는다(docs/sidecar.md 4절).
PROTOCOL = 1
_BOM = b"\xef\xbb\xbf"


def _roman_one(opt: LLMOutput):
    """꼬리말처럼 점역한다(`force_roman`, #54). 한글이 없는 로마자 조각에도 로마자표 `⠴` 를 붙인다(「한국 점자 규정」 제29항).

    점자 줄만 BE 가 꼬리말을 점역하는 `translate_plain` 과 같은 함수(`translate_with_breaks(force_roman=True)`)로 바꾸고,
    근거 · 글상자 테두리는 본문 길(`_translate_one`) 그대로 둔다. 본문 길은 로마숫자 단원명 `Ⅳ` 를 `⠠⠠⠊⠧` 로 적는데
    점자책 꼬리말은 `⠴⠠⠠⠊⠧` 다.
    """
    lines, breaks = translate_with_breaks(opt.corrected_text, force_roman=True)
    return _TB._translate_one(opt).model_copy(update={"braille_lines": lines, "break_points": breaks})


def translate(text: str, etype: str = "text", hlevel: int = 0,
              korean_grade1: bool = False, english_grade1: bool = False, math_page: bool = False,
              force_roman: bool = False, render_mode: str = "", tn_text: str = "", box_level: int = 0) -> dict:
    """요소 하나 → `flatten_elements` 가 내는 요소 본문(앞뒤 빈 줄 뺀 것, 32칸으로 안 접음) + 줄을 바꿔도 되는 자리
    + 점자에서 빠진 글자 + 점역 못 한 요소인가.

    표도 이 창구 하나로 된다(#60). `etype` 이 `table` 이거나 글이 표 태그(`<!표>`)로 읽히면 `table` 과 같은 길로
    가고, 응답에 `render_mode` · `drafts` 가 더 붙는다. 표만 쓰는 선택 칸이 `render_mode` · `tn_text` · `box_level`
    이다(뜻은 `table`). ★ 엔진만 표로 바꾸면 안 된다. `flatten_elements` 의 요소 type 도 `table` 이어야 한다.
    type 을 `text` 로 두면 표 줄마다 문단 들여쓰기 2칸이 더 붙어(`⠀⠀⠿⠿` → `⠀⠀⠀⠀⠿⠿`) 2027 dev · val 표
    900개가 900/900 다르다(`list_item` 도 900/900). 그 코퍼스에서 `<!표>` 가 든 요소는 표 요소 900개와 정확히
    같았다(표 아닌 요소 43,772개 중 0).

    꼬리말(`etype="header_footer"`)은 로마자 강제(`force_roman`)를 저절로 켠다(#60). 쓰는 자리가 꼬리말뿐이라
    앱이 따로 켤 일이 없다. `force_roman` 은 옛 호출을 위해 그대로 받는다.

    `flatten_elements` 를 그대로 부르고 `prefix` · `suffix` 를 떼며, `breaks` 는 `prefix` 길이만큼 뺀다.
    따로 세지 않는다. 종전에는 줄 사이 구분자를 늘 한 칸으로 세어, 앞 줄이 ⠀ 로 끝나 구분자가 빈 문자열인 자리
    뒤로 끊을 자리가 하나씩 밀렸다(#30). AI 응답 `TextElement.breaks` 와 같은 함수(`_flat_breaks`)다.

    `korean_grade1` · `english_grade1` 은 한글 정자 · 영어 1급이다(AI proto 의 같은 이름 필드). 엔진 문맥 값을
    이 호출 동안만 켠다. 사이드카는 오래 사는 프로세스라 켠 값이 다음 요청으로 새면 안 된다(#34).

    `math_page` 는 그 요소가 든 쪽이 수식 쪽이라는 뜻이다(`inline_math.MATH_PAGE`, #38). AI 서버는 쪽 PDF 의 한컴
    수식 글꼴 비율로 정하고, 수식 쪽이면 평문 속 `(1, 0)` · `p-q` 를 수식으로 적는다. 앱에서 수식 쪽 글을 다시
    점역할 때 넘겨야 서버가 낸 점자와 같다.

    점역은 AI 서버 체인과 같이 `TextBraille.translate`(= `isolation.safe_translate`)를 지난다(#52). 원문은 있는데
    점자가 0셀이거나 엔진이 예외를 던진 요소는 점역자 주 '점역 못 함'이 되고 `blocked` 가 참이다. 종전에는
    `_translate_one` 을 바로 불러 그런 요소가 빈 점자로 조용히 사라졌다(`dropped` 도 비어 표시가 없었다).
    """
    if etype == "table" or parse_table_tags(text) is not None:
        return table(text, render_mode, tn_text, box_level, korean_grade1, english_grade1, math_page)
    force_roman = force_roman or etype == "header_footer"
    opt = LLMOutput(element_id=uuid.uuid4(), corrected_text=text, routing_tier="ZERO")
    bo, fe = _run(opt, _roman_one if force_roman else _TB._translate_one, etype, hlevel,
                  korean_grade1, english_grade1, math_page)
    out = {"dropped": _dropped(text), "blocked": is_blocked_braille(bo.braille_lines)}   # AI 서버 검토 표시(C2 · R1)와 같은 판정
    if fe is None:                       # 내용이 없는 요소는 flatten_elements 가 담지 않는다
        return {"cells": "", "breaks": [], **out}
    return {**_body(fe, fe.text, fe.breaks), **out}


def table(source: str, render_mode: str = "", tn_text: str = "", box_level: int = 0,
          korean_grade1: bool = False, english_grade1: bool = False, math_page: bool = False) -> dict:
    """표 요소 하나 → 고른 안 + 다섯 안(풀어쓰기 · 격자 · 행열 바꿈 · 테두리만 · 번호 체계)의 요소 본문 (#56).

    `source` 는 표 태그 글(`<!표><!행><!칸>…`)이다. AI 응답 `TextElement.table_source` 가 이 값이다. 앱이 칸 글을
    고친 뒤 이 op 로 다시 점역하면 서버가 낸 표 점자와 같은 길(`TableBraille.translate` → `flatten_elements`)을
    지난다. `translate` 도 표 태그 글이나 `type="table"` 이면 이 길로 간다(#60). 이 op 는 한동안 같이 둔다.

    `render_mode` 는 고를 안(`unfold` · `table_grid` · `transposed` · `linear` · `numbered`)이다. 없거나 모르는
    값이면 풀어쓰기다(엔진 기본). `tn_text` 는 태그가 표로 안 풀리는 글일 때 대신 점역할 점역자 주 글이다.
    `box_level` 은 그 표를 감싼 글상자 위계다(서버 `_mark_table_box_levels`). 상자 안 표는 테두리를 한 단계
    아래 꼴로 그린다. 옵션 셋은 `translate` 와 같다.

    `cells` · `breaks` 는 고른 안이고 `drafts` 는 다섯 안 전부다(`render_mode` · `label` · `cells` · `breaks`).
    태그가 표로 안 풀리면 점역자 주 한 안이라 `drafts` 가 비고 `render_mode` 가 빈 문자열이다.
    """
    opt = LLMOutput(element_id=uuid.uuid4(), corrected_text=source, routing_tier="ZERO", render_mode=render_mode,
                    tn_text=tn_text or None)
    tb = TableBraille({opt.element_id: box_level} if box_level else None)
    bo, fe = _run(opt, tb._translate_one, "table", 0, korean_grade1, english_grade1, math_page)
    out = {"render_mode": bo.drafts[bo.selected_idx].render_mode if bo.drafts else "",
           "dropped": _dropped(source), "blocked": is_blocked_braille(bo.braille_lines)}
    if fe is None:
        return {"cells": "", "breaks": [], "drafts": [], **out}
    drafts = [{"render_mode": d.render_mode, "label": d.label, **_body(fe, t, b)}
              for d, t, b in zip(bo.drafts, fe.draft_texts, fe.draft_breaks)]
    return {**_body(fe, fe.text, fe.breaks), "drafts": drafts, **out}


def _run(opt: LLMOutput, translate_one, etype: str, hlevel: int,
         korean_grade1: bool, english_grade1: bool, math_page: bool):
    """요소 하나를 AI 서버 체인처럼 점역하고(`safe_translate`, #52) `flatten_elements` 로 편다 → (BrailleOutput, FlatElement).

    엔진 문맥 값(한글 정자 · 영어 1급 · 수식 쪽)은 이 호출 동안만 켠다. 사이드카는 오래 사는 프로세스라 켠 값이
    다음 요청으로 새면 안 된다(#34). 내용이 없는 요소는 `flatten_elements` 가 담지 않아 FlatElement 가 None 이다.
    """
    tokens = KOREAN_GRADE1.set(korean_grade1), ENGLISH_GRADE1.set(english_grade1), inline_math.MATH_PAGE.set(math_page)
    try:
        bo = safe_translate([opt], translate_one)[0]
        el = SimpleNamespace(element_id=bo.element_id, type=etype, reading_order=0, heading_level=hlevel)
        return bo, flatten_elements([bo], SimpleNamespace(elements=[el])).get(bo.element_id)
    finally:
        KOREAN_GRADE1.reset(tokens[0])
        ENGLISH_GRADE1.reset(tokens[1])
        inline_math.MATH_PAGE.reset(tokens[2])


def _body(fe, text: str, breaks) -> dict:
    """요소 통 문자열에서 앞뒤 빈 줄(`prefix` · `suffix`)을 떼고, 끊을 자리를 `prefix` 길이만큼 당긴다."""
    n = len(fe.prefix)
    return {"cells": text[n:len(text) - len(fe.suffix)], "breaks": [b - n for b in breaks]}


def _dropped(text: str) -> list[dict]:
    return [{"text": t, "count": n, "flag": flag} for flag, count in _DROPPED for t, n in count(text).most_common()]


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
                         _flag(req, "korean_grade1"), _flag(req, "english_grade1"), _flag(req, "math_page"),
                         _flag(req, "force_roman"), req.get("render_mode") or "", req.get("tn_text") or "",
                         int(req.get("box_level") or 0))
    if op == "table":
        return table(req.get("table_source") or "", req.get("render_mode") or "", req.get("tn_text") or "",
                     int(req.get("box_level") or 0), _flag(req, "korean_grade1"), _flag(req, "english_grade1"),
                     _flag(req, "math_page"))
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
        return {"ok": True, "version": __version__, "protocol": PROTOCOL}
    return {"error": f"모르는 op: {op!r}"}


def _answer(raw: bytes) -> dict | None:
    """표준입력 한 줄(바이트) → 응답. 빈 줄(공백뿐인 줄 포함)에는 응답하지 않아 None 이다.

    줄마다 UTF-8 로 푼다. 종전에는 `sys.stdin` 을 플랫폼 인코딩으로 풀다가 못 푸는 바이트에서 프로세스가 죽었다
    (한국어 Windows 의 cp949 표준입력에 UTF-8 한글 · 깨진 바이트 0xff, #44). 이제 그 줄만 `error` 로 답하고 계속 돈다.
    줄 머리 UTF-8 BOM 은 뗀다(C# `StreamWriter` 를 BOM 있는 `Encoding.UTF8` 로 만들면 첫 줄 앞에 붙는다).
    """
    if raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    if not raw.strip():
        return None
    req = {}
    try:
        line = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        try:                              # 짝짓기에 쓰는 id 만 건진다. 깨진 글로 점역하지는 않는다
            req = json.loads(raw.decode("utf-8", "replace"))
        except ValueError:
            pass
        res = {"error": f"UnicodeDecodeError: 표준입력은 UTF-8 이어야 한다({exc.start}번째 바이트 0x{raw[exc.start]:02x})"}
    else:
        try:
            req = json.loads(line)
            res = handle(req)
        except Exception as exc:          # 한 요청이 실패해도 사이드카는 산다
            res = {"error": f"{type(exc).__name__}: {exc}"}
    res["id"] = req.get("id") if isinstance(req, dict) else None
    return res


def main() -> None:
    threading.Thread(target=decode, args=(_WARMUP,), kwargs={"english": True}, daemon=True).start()
    for raw in sys.stdin.buffer:          # 바이트로 읽는다. 표준입력 인코딩(cp949 등)에 끌려가지 않는다
        res = _answer(raw)
        if res is not None:
            sys.stdout.write(json.dumps(res, ensure_ascii=True) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
