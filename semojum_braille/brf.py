"""`.brf` 파일 꼴. 점자 면 배열을 현장 유통본과 같은 바이트로 낸다.

꼴은 셋이다.

- 줄 끝은 `\\r\\n` 이다.
- 쪽마다 끝에 `\\x0c`(폼 피드)를 둔다. 마지막 쪽도 같다.
- 글자는 BRF ASCII 뿐이고, 한 줄은 32칸을 넘지 않는다. 한 쪽은 26줄이다.

근거는 현장 점자 파일 실측이다(2026-10-04, 99권 522개 파일). 522개 모두 CR 수 = LF 수 = `\\r\\n` 수다.
FF 로 나눈 쪽이 26줄인 파일이 506개, FF 로 끝나는 파일이 432개다. 점자 규정과 제작 지침에는 파일의
바이트 꼴을 정한 조항이 없다(「점자 도서 제작 지침」 1장 5 는 파일 이름만 정한다).
"""
from __future__ import annotations

import logging
from collections import Counter

from .encoder.gates import gate_hit

logger = logging.getLogger(__name__)

ROWS = 26
COLS = 32

# BRF Braille ASCII 64셀 표(유니코드 오프셋 0..63 순). braille-assist 와 같은 표다.
# 글자 꼴은 현장 파일 다수를 따른다. 522개 중 312개(60%)가 **영문자 소문자 + ⠈ 는 백틱(`` ` ``) + `[ \\ ] ^` 그대로**다.
# 190개(36%)는 영문자 대문자 + ⠈ 는 `@` 이고, 20개는 소문자 + `@` 다. 점자 도서 코퍼스(1,131개)도
# 소문자 + 백틱 606 · 대문자 + `@` 525 로 같은 두 꼴이다. 읽는 쪽은 대소문자를 안 가린다.
# ⚠ braille-assist `to_brf_ascii` 는 소문자 + `@` + `{ | } ~` 로 냈다. 현장 파일에는 거의 없는 섞임 꼴이라 따르지 않는다
#   (소문자 파일 312개에서 `{` 557 · `|` 635 · `}` 130 · `~` 71 자 대 `[` 39만 · `\\` 4만 · `]` 23만 · `^` 41만 자).
_BRAILLE_ASCII = (
    " A1B'K2L@CIF/MSP"
    '"E3H9O6R^DJG>NTQ'
    ",*5<-U8V.%[$+X!&"
    ";:4\\0Z7(_?W]#Y)="
)
_CELL_TO_ASCII = {chr(0x2800 + i): "`" if ch == "@" else ch.lower() for i, ch in enumerate(_BRAILLE_ASCII)}


def to_brf_ascii(braille: str) -> str:
    """유니코드 점자 → BRF ASCII. 빈칸 셀 `⠀` 와 ASCII 공백은 공백으로, 줄바꿈은 그대로 둔다.

    못 푸는 글자는 `⟨XXXX⟩` 로 남긴다(조용히 버리지 않는다). 파일로 쓸 때는 `serialize_brf` 가 그걸 막는다.

    >>> to_brf_ascii("⠼⠁⠃⠀⠈⠣")
    '#ab `<'
    """
    out = []
    for ch in braille:
        if ch == "\n":
            out.append("\n")
        elif ch in ("⠀", " "):
            out.append(" ")
        else:
            a = _CELL_TO_ASCII.get(ch)
            out.append(f"⟨{ord(ch):04X}⟩" if a is None else a)
    return "".join(out)


def serialize_brf(pages: list[list[str]], *, rows: int = ROWS, cols: int = COLS,
                  replaced: Counter | None = None) -> bytes:
    """점자 면 배열 → `.brf` 바이트.

    `pages` 는 면마다 줄 목록이다(유니코드 점자. BRF ASCII 를 줘도 된다). 줄이 `rows` 보다 적은 면은
    빈 줄로 채운다. 면이 `rows` 줄을 넘거나, 줄이 `cols` 칸을 넘거나, 줄 안에 줄바꿈이 있으면 `ValueError` 다
    (조판 결함이다).

    BRF ASCII 로 못 옮기는 글자(점자 블록 64셀 밖, 가는 띄움 U+2009 등)는 **빈칸으로 바꿔 내보낸다**.
    고객 문서를 못 내보내는 것이 더 나쁘다(대표 결재 2026-10-04). 대신 삼켜지지 않게 셋으로 알린다:
    G4 관문 계수(`gate_hit("G4", "BRF빈칸대체", n)`), WARNING 로그, `replaced` 에 넘긴 Counter(글자 → 횟수).
    근본은 점역기가 막는다(Semojum/AI#1069). 여기는 마지막 방어선이다.

    >>> serialize_brf([["⠼⠁", "⠁⠃"]], rows=3)
    b'#a\\r\\nab\\r\\n\\r\\n\\x0c'
    """
    out: list[str] = []
    bad: Counter = Counter()
    for p, page in enumerate(pages, 1):
        if len(page) > rows:
            raise ValueError(f"{p}면이 {len(page)}줄이다(최대 {rows}줄)")
        for k, line in enumerate(list(page) + [""] * (rows - len(page)), 1):
            if "\n" in line or "\r" in line:
                raise ValueError(f"{p}면 {k}줄 안에 줄바꿈이 있다")
            cells = []
            for ch in line:
                a = " " if ch in ("⠀", " ") else _CELL_TO_ASCII.get(ch, ch if " " <= ch <= "~" else None)
                if a is None:
                    bad[ch] += 1
                    a = " "
                cells.append(a)
            a = "".join(cells)
            if len(a) > cols:
                raise ValueError(f"{p}면 {k}줄이 {len(a)}칸이다(최대 {cols}칸)")
            out.append(a + "\r\n")
        out.append("\x0c")
    if bad:
        n = sum(bad.values())
        gate_hit("G4", "BRF빈칸대체", n)
        logger.warning("G4 BRF 에 못 옮기는 글자 %d자를 빈칸으로 바꿨다 (%s)", n,
                       " ".join(f"U+{ord(c):04X}×{k}" for c, k in bad.most_common()))
        if replaced is not None:
            replaced.update(bad)
    return "".join(out).encode("ascii")
