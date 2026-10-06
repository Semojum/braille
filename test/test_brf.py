"""`.brf` 꼴 시험. 내용이 아니라 바이트 꼴(CR · LF · FF 수, 쪽마다 줄 수, 줄 폭, 글자)을 단언한다.

현장 점자 파일은 저작물이라 저장소에 넣지 않는다. 환경변수 `SEMOJUM_FIELD_BRF` 가 그 파일들이 든 폴더를
가리키면, 현장 파일을 읽어 우리 직렬화로 다시 쓴 바이트가 원본과 같은지까지 본다. 없으면 그 시험은 건너뛴다.
"""
import os
from pathlib import Path

import pytest

from semojum_braille.brf import (COLS, ROWS, from_brf_ascii, looks_like_ascii_braille, parse_brf,
                                  serialize_brf, to_brf_ascii)


def _form(b: bytes) -> dict:
    """바이트 꼴. 현장 파일과 우리 출력을 같은 잣대로 잰다."""
    pages = b.split(b"\x0c")
    tail = pages.pop()                       # FF 로 끝나면 빈 토막이 남는다
    return {
        "cr=lf=crlf": b.count(b"\r") == b.count(b"\n") == b.count(b"\r\n"),
        "ends_ff": tail == b"",
        "pages": len(pages),
        "rows": {p.count(b"\r\n") for p in pages},
        "lines_end_crlf": all(p.endswith(b"\r\n") for p in pages),
        "max_cols": max((len(ln) for p in pages for ln in p.split(b"\r\n")), default=0),
        "ascii": all(32 <= c <= 126 or c in (10, 12, 13) for c in b),
    }


def test_꼴_세_가지가_선다():
    b = serialize_brf([["⠼⠁⠃", "⠈⠣⠀⠘⠪"], ["⠿" * COLS]])
    f = _form(b)
    assert f == {"cr=lf=crlf": True, "ends_ff": True, "pages": 2, "rows": {ROWS},
                 "lines_end_crlf": True, "max_cols": COLS, "ascii": True}


def test_짧은_면은_빈_줄로_채우고_마지막_면도_FF_로_끝난다():
    b = serialize_brf([["⠁"]])
    assert b == b"a\r\n" + b"\r\n" * (ROWS - 1) + b"\x0c"


def test_글자_꼴은_소문자와_백틱이다():
    # ⠈(초성 ㄱ)는 백틱, ⠪ ⠻ ⠳ ⠘ 는 [ ] \ ^ 그대로(현장 파일 다수 꼴)
    assert to_brf_ascii("⠈⠪⠻⠳⠘⠁⠵") == "`[]\\^az"


def test_빈_목록은_빈_파일():
    assert serialize_brf([]) == b""


@pytest.mark.parametrize("pages, msg", [
    ([["⠁"] * (ROWS + 1)], "줄이다"),
    ([["⠁" * (COLS + 1)]], "칸이다"),
    ([["⠁\n⠃"]], "줄바꿈"),
    ([["가"]], "못 옮기는"),
])
def test_잘못된_꼴은_내지_않는다(pages, msg):
    with pytest.raises(ValueError, match=msg):
        serialize_brf(pages)


def _field_files() -> list[Path]:
    d = os.environ.get("SEMOJUM_FIELD_BRF")
    if not d:
        return []
    out = []
    for f in sorted(Path(d).rglob("*.brf")):
        b = f.read_bytes()
        f0 = _form(b)
        # 우리가 따르는 꼴(소문자 + 백틱, FF 로 끝남, 쪽마다 26줄)인 현장 파일만 고른다.
        # 2026-10-04 실측: 이 꼴 219개 중 166개가 바이트까지 같다. 53개는 `{ | } ~` 를 `[ \\ ] ^` 와 섞어 써서
        # 한 표로 되쓸 수 없고(52개), 1개는 33칸 줄이 있다.
        if (f0["ends_ff"] and f0["rows"] == {ROWS} and not any(65 <= c <= 90 for c in b)
                and not any(ch in b for ch in (b"@", b"{", b"|", b"}", b"~"))):
            out.append(f)
        if len(out) == 5:
            break
    return out


@pytest.mark.skipif(not os.environ.get("SEMOJUM_FIELD_BRF"), reason="현장 점자 파일 폴더(SEMOJUM_FIELD_BRF)가 없다")
def test_현장_파일을_다시_쓰면_바이트가_같다():
    files = _field_files()
    assert len(files) == 5, "고른 현장 파일이 다섯이 안 된다"
    for f in files:
        b = f.read_bytes()
        assert serialize_brf(parse_brf(b)) == b, f.name
        assert _form(b)["cr=lf=crlf"] and _form(b)["max_cols"] <= COLS, f.name


# ── 읽기(parse_brf · from_brf_ascii) ──────────────────────────────────────────

def test_읽기는_쓰기의_짝이다():
    pages = [["⠼⠁⠃", "⠈⠣⠀⠘⠪"], ["⠿" * COLS]]
    assert parse_brf(serialize_brf(pages)) == [p + [""] * (ROWS - len(p)) for p in pages]


def test_현장_두_꼴을_다_받는다():
    # 소문자 + 백틱(현장 60%) · 대문자 + @(36%) · 시프트형 { | } ~
    assert from_brf_ascii("#ab `<") == from_brf_ascii("#AB @<") == "⠼⠁⠃⠀⠈⠣"
    assert from_brf_ascii("{|}~") == from_brf_ascii("[\\]^") == "⠪⠳⠻⠘"


def test_백틱은_기본이_초성_ㄱ_이다():
    # `.brf` 를 space 로 읽으면 초성 ㄱ 이 사라진다. 기본값이 cell 인 이유.
    assert from_brf_ascii("`m`") == "⠈⠍⠈"
    assert from_brf_ascii("`m`", backtick="space") == "⠀⠍⠀"


def test_우리가_낸_파일을_읽어_역점역하면_원문이다():
    from semojum_braille.decoder import decode
    from semojum_braille.encoder.translator import translate_tagged_text
    src = "국가 관련 기관은 고구마를 키운다."
    [[line, *_]] = parse_brf(serialize_brf([[translate_tagged_text(src)]]))
    assert decode(line) == src


def test_탭은_4칸_자리로_펼친다():
    # 현장 파일 5개가 쪽 번호를 오른쪽에 맞추는 데 탭을 쓴다. 4칸으로 펼치면 32칸이다.
    [[line]] = parse_brf("\t" * 7 + "  #d\r\n")
    assert len(line) == COLS and line.endswith("⠼⠙")


def test_BRF_ASCII_아닌_글자는_예외():
    with pytest.raises(ValueError, match="BRF ASCII 가 아니다"):
        from_brf_ascii("ab한")


def test_유니코드_점자가_있으면_ASCII_가_아니다():
    assert looks_like_ascii_braille("#ab `<") and not looks_like_ascii_braille("⠼⠁")


@pytest.mark.skipif(not os.environ.get("SEMOJUM_FIELD_BRF"), reason="현장 점자 파일 폴더(SEMOJUM_FIELD_BRF)가 없다")
def test_현장_파일은_다_읽힌다():
    files = sorted(Path(os.environ["SEMOJUM_FIELD_BRF"]).rglob("*.brf"))
    assert files
    for f in files:
        assert parse_brf(f.read_bytes()), f.name
