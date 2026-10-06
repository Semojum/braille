"""`.brf` 파일 꼴. 점자 면 배열을 현장 유통본과 같은 바이트로 내고(`serialize_brf`), 거꾸로 읽는다(`parse_brf`).

꼴은 셋이다.

- 줄 끝은 `\\r\\n` 이다.
- 쪽마다 끝에 `\\x0c`(폼 피드)를 둔다. 마지막 쪽도 같다.
- 글자는 BRF ASCII 뿐이고, 한 줄은 32칸을 넘지 않는다. 한 쪽은 26줄이다.

근거는 현장 점자 파일 실측이다(2026-10-04, 99권 522개 파일). 522개 모두 CR 수 = LF 수 = `\\r\\n` 수다.
FF 로 나눈 쪽이 26줄인 파일이 506개, FF 로 끝나는 파일이 432개다. 점자 규정과 제작 지침에는 파일의
바이트 꼴을 정한 조항이 없다(「점자 도서 제작 지침」 1장 5 는 파일 이름만 정한다).
"""
from __future__ import annotations

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
# 읽기: 대소문자를 안 가리고, 소문자 시프트형 `` ` { | } ~ `` 를 `@ [ \ ] ^` 로 본다(현장 두 꼴을 다 받는다).
_ASCII_TO_CELL = {ch: chr(0x2800 + i) for i, ch in enumerate(_BRAILLE_ASCII)}
_ASCII_TO_CELL.update({ch.lower(): c for ch, c in _ASCII_TO_CELL.items() if ch.isalpha()})
_ASCII_TO_CELL.update({"`": "⠈", "{": "⠪", "|": "⠳", "}": "⠻", "~": "⠘"})
_ASCII_TO_CELL[" "] = "⠀"


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


def serialize_brf(pages: list[list[str]], *, rows: int = ROWS, cols: int = COLS) -> bytes:
    """점자 면 배열 → `.brf` 바이트.

    `pages` 는 면마다 줄 목록이다(유니코드 점자. BRF ASCII 를 줘도 된다). 줄이 `rows` 보다 적은 면은
    빈 줄로 채운다. 면이 `rows` 줄을 넘거나, 줄이 `cols` 칸을 넘거나, 줄 안에 줄바꿈이 있거나,
    BRF ASCII 로 못 옮기는 글자가 있으면 `ValueError` 다. 파일을 잘못된 꼴로 내지 않는다.

    >>> serialize_brf([["⠼⠁", "⠁⠃"]], rows=3)
    b'#a\\r\\nab\\r\\n\\r\\n\\x0c'
    """
    out: list[str] = []
    for p, page in enumerate(pages, 1):
        if len(page) > rows:
            raise ValueError(f"{p}면이 {len(page)}줄이다(최대 {rows}줄)")
        for k, line in enumerate(list(page) + [""] * (rows - len(page)), 1):
            if "\n" in line or "\r" in line:
                raise ValueError(f"{p}면 {k}줄 안에 줄바꿈이 있다")
            a = to_brf_ascii(line)
            if any(not (" " <= c <= "~") for c in a):
                raise ValueError(f"{p}면 {k}줄에 BRF ASCII 로 못 옮기는 글자가 있다: {a!r}")
            if len(a) > cols:
                raise ValueError(f"{p}면 {k}줄이 {len(a)}칸이다(최대 {cols}칸)")
            out.append(a + "\r\n")
        out.append("\x0c")
    return "".join(out).encode("ascii")


def looks_like_ascii_braille(text: str) -> bool:
    """유니코드 점자 셀(U+2800~U+28FF)이 하나도 없으면 BRF ASCII 로 본다."""
    return not any("\u2800" <= c <= "\u28ff" for c in text)


def from_brf_ascii(text: str, *, backtick: str = "cell") -> str:
    """BRF ASCII → 유니코드 점자. `to_brf_ascii` 의 짝이다. 공백은 빈칸 셀 `⠀` 로, 줄바꿈은 그대로 둔다.

    backtick — 백틱(`` ` ``)을 무엇으로 볼지. **기본 "cell" 을 바꾸지 말 것.**
      "cell"  = ⠈(초성 ㄱ). `.brf` 파일(현장 유통본 · 점자 도서 코퍼스 · 우리 `serialize_brf`)의 관례다.
      "space" = 칸 띄우기. 「한국 점자 규정」 원문의 점자 예시를 옮겨 적을 때만 쓴다(줄 끝 채움 백틱).
    `.brf` 를 "space" 로 읽으면 초성 ㄱ 이 전부 사라진다(`국가 관련` → `욱가 완련`). 오류 없이 틀린다.

    BRF ASCII 가 아닌 글자가 있으면 `ValueError` 다(조용히 버리지 않는다).

    >>> from_brf_ascii("#ab `<")
    '⠼⠁⠃⠀⠈⠣'
    >>> from_brf_ascii("#AB @<") == from_brf_ascii("#ab `<")
    True
    """
    if backtick not in ("cell", "space"):
        raise ValueError(f"backtick 은 'cell' 또는 'space': {backtick!r}")
    out = []
    for k, ch in enumerate(text):
        if ch == "\n":
            out.append(ch)
        elif ch == "`" and backtick == "space":
            out.append("⠀")
        else:
            c = _ASCII_TO_CELL.get(ch)
            if c is None:
                raise ValueError(f"{k}번째 글자 {ch!r} 는 BRF ASCII 가 아니다")
            out.append(c)
    return "".join(out)


def parse_brf(data: bytes | str, *, backtick: str = "cell") -> list[list[str]]:
    """`.brf` 바이트 → 점자 면 배열(면마다 유니코드 점자 줄 목록). `serialize_brf` 의 짝이다.

    줄 끝은 `\\r\\n` · `\\n` 을 다 받고, 쪽은 `\\x0c` 로 나눈다. 마지막 `\\x0c` 뒤가 비어 있으면 면을 하나 더
    만들지 않는다. 줄 끝 빈칸은 그대로 둔다. 앱은 이 줄을 `decoder.decode` 에 넘겨 역점역한다.

    >>> parse_brf(b"#a\\r\\nab\\r\\n\\r\\n\\x0c")
    [['⠼⠁', '⠁⠃', '']]
    """
    text = data.decode("ascii") if isinstance(data, bytes) else data
    pages = text.replace("\r\n", "\n").split("\x0c")
    if len(pages) > 1 and pages[-1].strip("\n") == "":
        pages.pop()
    # 탭은 4칸 탭 자리로 펼친다. 현장 파일 522개 중 5개가 쪽 번호를 오른쪽에 맞추는 데 탭을 썼고(143자),
    # 탭 든 줄 23개가 4칸으로 펼치면 전부 정확히 32칸이다(8칸이면 44~60칸으로 넘친다).
    return [[from_brf_ascii(line.expandtabs(4), backtick=backtick) for line in page.removesuffix("\n").split("\n")]
            for page in pages]
