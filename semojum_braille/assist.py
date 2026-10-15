"""점자 조판 공용 함수: 면 나누기 · 줄 자르기 · 페이지행 · 원본 페이지 변경선 · BRF 조립.

braille-assist(`python/braille_assist/core.py`, develop 2c41d8d)에서 옮겨 왔다(2026-10-04). 파이썬 기준 구현은
이제 여기다. 같은 함수의 ts(`ts/`) · java(`java/`) 판도 braille-assist develop 38e21e2 에서 이 저장소로 옮겨 왔다
(2026-10-09). 동작 명세는 루트 `vectors.json`(0.5.0, 줄바꿈 두 갈래) 하나다. 파이썬은 `test/test_assist_vectors.py`,
ts · java 는 `.github/workflows/assist.yml` 이 같은 파일로 맞춘다. 규칙을 바꾸면 세 구현과 벡터를 한 PR 로 고친다.

이 모듈은 한글을 점역하지 않는다. 이미 점역된 점자를 받아 배치만 한다.
근거: 「점자 도서 제작 지침」 1장 2절 2(페이지 구성) · 1장 3(꼬리말) · 2장 2절 2-3(원본 페이지 변경선).

★ 파일로 낼 때는 `build_brf_file` 을 쓴다(현장 꼴 `.brf` 바이트, `semojum_braille.brf`).
  `build_brf` · `to_brf_ascii` 는 벡터가 묶은 옛 꼴(줄 끝 `\n`, FF 없음, `{ | } ~` · `@`)이라 그대로 둔다.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass

from .brf import serialize_brf

SPACE = "⠀"          # 공백 셀 ⠀
NUM_SIGN = "⠼"       # 수표 ⠼
CHANGE_MARK = "⠤"    # 원본 페이지 변경선 채움 ⠤
WRAP_MODES = ("syllable", "word")   # 줄바꿈 두 갈래(2026-10-10 대표 확정, 기본 음절. 10-09 의 점자 칸 갈래는 뺐다)
_TN_MARK = "⠠⠄"     # 점역자 주 표(두 칸). 강제로 자를 때 가르지 않는다

# 숫자·알파벳은 같은 점형을 쓴다(1=a=⠁ … 0=j=⠚). 수표가 앞에 오면 숫자로 읽는다.
_DIGIT_CELLS = "⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊"  # 0..9 = j a b c d e f g h i
_ALPHA_CELLS = (
    "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚"  # a..j
    "⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞"  # k..t
    "⠥⠧⠺⠭⠽⠵"                          # u..z
)

# BRF Braille ASCII 64셀 표준표(유니코드 오프셋 0..63 순). 출처는 `code/AI/app/utils/braille_ascii.py`와
# 같은 표 — 여기 새로 만들지 않고 그대로 옮겼다(backtick=⠈ 사고 전례가 있어 임의 변형 금지).
_BRAILLE_ASCII = (
    " A1B'K2L@CIF/MSP"
    '"E3H9O6R^DJG>NTQ'
    ",*5<-U8V.%[$+X!&"
    ";:4\\0Z7(_?W]#Y)="
)
assert len(_BRAILLE_ASCII) == 64


@dataclass(frozen=True)
class Options:
    """조판 옵션. 1차 PoC 고정값이 기본값이다(조판 가이드 §5).

    page_row_on — 페이지행을 넣는 면. **기본은 홀수 면만**이다(2026-08-06 변경).
      지침 1장2절2-1이 홀수 면만이라 하고, 점자 도서 82권 실측에서도 페이지행을 가진 면이
      100% 홀수였다(원장 C-11 — 규정=관행 확정). 종전 기본값 "every"는 규정과 어긋났다.
      `every`·`even`·`none`으로 바꿀 수 있다 — 고정이 아니라 기본값일 뿐이다.

    cover_pages — **원본 페이지 개수**다. 점자 면 수가 아니다(2026-09-01 확정).
      앞에서 이만큼의 원본 페이지를 표지로 보고 ① 페이지행을 넣지 않고 ② 본문 번호를
      그 뒤부터 센다. `orig_page_start`와 함께 계산된다.
      ③ **점자 면 번호도 소비하지 않는다**(2026-09-08). 지침 1장2 3)(1)(도서 335행)
      "점자 페이지 번호는 점자 표지 다음 페이지를 1로 시작"·604행 "점자 표지에는 점자
      페이지 번호를 적지 않는다"·자료지침 §2.1.5(1)(557행). 종전에는 표지 면이 번호를
      먹어 본문 첫 면이 2·3번이 됐다.

    orig_page_start — 표지 다음 첫 본문 원본 페이지에 붙일 번호.
      None이면 `sources`가 준 `orig_page`를 그대로 쓴다(종전 동작).
      값을 주면 **표지 뒤 n번째 원본 페이지 = orig_page_start + n** 으로 다시 매긴다.

    show_change_line — 원본 페이지 변경선(원본 페이지 내용이 끝난 다음 줄, 새 원본 페이지
      번호만 적는 줄). 끄면 그 줄을 아예 넣지 않는다.
      ⚠ `show_orig_page`를 끄면 변경선에 적을 번호가 없어 `⠤`만 남은 빈 줄이 된다.
      그래서 `show_orig_page=False`면 변경선도 함께 꺼진다(2026-09-01 결정 D).

    footer_align — 꼬리말 정렬. `center`(지침 1장3-1 기본) · `right` · `left`(V4 가이드).
      right는 점자 페이지 번호 왼쪽에 **두 칸을 띄운 자리**가 오른쪽 끝이다(항목 사이 두 칸 이상).
      left는 원본 페이지 번호 오른쪽에 두 칸을 띄운 자리(번호가 없으면 첫 칸)에서 시작한다.

    pad_to_even — 홀수 면에서 끝나면 빈 면 하나를 더한다(V4 가이드). 더한 면도 다른 면과 같은 페이지행 규칙을 따른다.

    wrap — 32칸을 넘는 줄을 접는 갈래. `syllable`(기본) · `word` 두 갈래다(2026-10-10 대표 확정).
      뜻은 `wrap()` 에 적었다. 블록에 `breaks` 가 없으면 `syllable` 이어도 `word` 로 접는다.
    """

    cols: int = 32
    rows: int = 26
    show_orig_page: bool = True      # 페이지행 왼쪽의 원본 페이지 번호
    show_braille_page: bool = True   # 페이지행 오른쪽의 점자 페이지 번호
    page_row_on: str = "odd"         # odd | every | even | none
    cover_pages: int = 0             # 앞에서 이만큼의 **원본 페이지**가 표지 (아래 주석)
    orig_page_start: int | None = None   # 본문 첫 원본 페이지에 붙일 번호. None이면 준 값 그대로
    show_change_line: bool = True    # 원본 페이지 변경선을 넣을지
    footer_align: str = "center"     # center | right | left
    wrap: str = "syllable"           # syllable | word
    pad_to_even: bool = False        # 홀수 면에서 끝나면 빈 면 하나를 더한다

    def __post_init__(self) -> None:
        if self.cols < 8:
            raise ValueError(f"cols는 8 이상이어야 한다: {self.cols}")
        if self.page_row_on not in ("every", "odd", "even", "none"):
            raise ValueError(f"page_row_on은 odd|every|even|none: {self.page_row_on!r}")
        if self.footer_align not in ("center", "right", "left"):
            raise ValueError(f"footer_align은 center|right|left: {self.footer_align!r}")
        if self.cover_pages < 0:
            raise ValueError(f"cover_pages는 0 이상이어야 한다: {self.cover_pages}")
        if self.wrap not in WRAP_MODES:
            raise ValueError(f"wrap은 syllable|word: {self.wrap!r}")


DEFAULT = Options()


def _number(n: int) -> str:
    """정수 → 수표 + 숫자 점형. 예: 12 → ⠼⠁⠃"""
    if n < 0:
        raise ValueError(f"페이지 번호는 0 이상이어야 한다: {n}")
    return NUM_SIGN + "".join(_DIGIT_CELLS[int(d)] for d in str(n))


def _alpha(idx: int) -> str:
    """걸침 순번 → 알파벳 점형. 1→a, 2→b … 26→z, 27→aa(두 글자).

    지침 1장2절2-2(3): 원본 한 쪽이 여러 점자 면에 걸치면 **두 번째 면부터**
    번호 **앞에** 로마자표 없이 알파벳을 순차로 적는다. 그래서 idx는 1부터다.
    실물 [예 1-7]에서 105면(0)·107면(2=b)·109면(4=d) — 면 순번이지 페이지행 순번이 아니다.
    """
    if idx <= 0:
        return ""
    out = ""
    while idx > 0:
        idx, r = divmod(idx - 1, 26)
        out = _ALPHA_CELLS[r] + out
    return out


def page_row(
    orig_page: int,
    cont_idx: int,
    braille_page: int,
    footer: str = "",
    opts: Options = DEFAULT,
) -> str:
    """페이지행 1줄(폭 = opts.cols)을 만든다.

    지침 1장2절2·1장3:
      · 원본 쪽 번호 — 왼쪽 정렬, 첫 칸. cont_idx≥1이면 번호 **앞에** 알파벳(로마자표 없이)
      · 꼬리말 — 가운데 정렬, 항목 사이 **두 칸 이상**
      · 점자 면 번호 — 오른쪽 정렬

    ★ 가운데 정렬은 **올림**이다: start = (cols - len(footer) + 1) // 2.
    지침 실물 4건([예 1-6]·[예 1-7]×3·[예 1-8])이 전부 이 값과 일치한다.
    내림으로 하면 [예 1-6](꼬리말 13칸)이 1칸 어긋난다.
    ⚠ 조판 가이드(2026-08-05) §4의 호출 예 두 개는 이 규칙과 다르다 — 예1은 33칸이라
    폭 자체가 틀렸고 예2는 시작 칸이 2 어긋난다. **지침 실물이 정본이다.**

    footer는 이미 점역된 점자 문자열이다(이 함수는 점역하지 않는다).
    자리에 안 들어가면 지침 1장3-4)에 따라 **뒤에서 잘라** 넣는다.
    """
    n = opts.cols
    left = ""
    if opts.show_orig_page:
        left = _alpha(cont_idx) + _number(orig_page)
    right = _number(braille_page) if opts.show_braille_page else ""

    if len(left) + len(right) > n:
        raise ValueError(f"쪽 번호만으로 {n}칸을 넘는다: 원본 {len(left)} + 점자 {len(right)}")

    cells = [SPACE] * n
    for i, c in enumerate(left):
        cells[i] = c
    for i, c in enumerate(right):
        cells[n - len(right) + i] = c

    if footer:
        # 항목 사이 두 칸 이상(지침 1장3-1). 좌우 여백을 뺀 자리에만 놓는다.
        lo = len(left) + 2 if left else 0
        hi = n - len(right) - 2 if right else n
        room = hi - lo
        f = footer[:room] if len(footer) > room else footer
        if f:
            if opts.footer_align == "right":
                start = hi - len(f)                # 오른쪽 끝(번호와 두 칸 띄운 자리)에 붙인다
            elif opts.footer_align == "left":
                start = lo                         # 왼쪽 끝(원본 번호와 두 칸 띄운 자리)에서 시작한다
            else:
                start = (n - len(f) + 1) // 2      # ★ 올림 — 지침 실물로 확정
            start = min(max(start, lo), hi - len(f))
            for i, c in enumerate(f):
                cells[start + i] = c

    return "".join(cells)


def page_change_line(orig_page: int, opts: Options = DEFAULT) -> str:
    """원본 페이지 변경선 1줄. 지침 2장2절2-3: 첫 칸부터 ⠤로 채우고 오른쪽 끝에 새 원본 쪽 번호.

    실물 [예 1-7]·[예 1-8]: `-----------------------------#gb` — 채움 29칸 + 번호 3칸 = 32.
    """
    n = opts.cols
    num = _number(orig_page) if opts.show_orig_page else ""
    if len(num) > n:
        raise ValueError(f"쪽 번호가 {n}칸을 넘는다: {len(num)}")
    return CHANGE_MARK * (n - len(num)) + num


_CELL_TO_ASCII = {chr(0x2800 + i): ch for i, ch in enumerate(_BRAILLE_ASCII)}
# 표준 ASCII `[ \ ] ^` 는 지침 표기에서 시프트형 `{ | } ~` 로 나온다.
_UNSHIFT = {"[": "{", "\\": "|", "]": "}", "^": "~"}


def to_brf_ascii(braille: str) -> str:
    """유니코드 점자 → BRF-ASCII(소문자). 파일에 쓰기 직전에 한 번 호출한다.

    공백 셀 ⠀는 **리터럴 스페이스**로 낸다(조판 가이드 §3: `⠼⠛⠀⠀…` → `#g  …`).
    ⚠ 코퍼스 `.brl` 관례의 백틱(``` ` ``` = ⠈ = 초성 ㄱ)과 혼동 금지 — 여기서 백틱을 공백으로
    쓰면 초성 ㄱ이 통째로 사라진다(2026-07-13 채점 붕괴 전례).
    줄바꿈은 보존한다. 못 푸는 셀은 `⟨XXXX⟩`로 남긴다(조용히 버리지 않는다).
    """
    out: list[str] = []
    for ch in braille:
        if ch == "\n":
            out.append("\n")
        elif ch == SPACE or ch == " ":
            out.append(" ")
        else:
            a = _CELL_TO_ASCII.get(ch)
            out.append(f"⟨{ord(ch):04X}⟩" if a is None else _UNSHIFT.get(a, a.lower()))
    return "".join(out)


# ── 문서 조립 (2026-08-05 추가) ──────────────────────────────────────────────
# 왜 여기 있나: ① 어느 면에 페이지행을 넣나 ② 걸침 순번(a·b·c)을 어떻게 세나
# ③ 표지를 어디까지 빼나 — 셋 다 **지침 규칙**이다. 호출자(BE·FE)가 각자 구현하면
# 점자 규정이 레포 밖으로 흩어진다. 이 레포를 만든 이유가 그걸 막으려는 것이다.
# (2026-08-05 사용자 결정으로 함수 3개 → 4개. 초판은 "typeset 엔진 공용화 안 함"이었다.)


# 해설 정답 목록(`01 ①  02 ③  03 ④`)은 쌍 안(번호와 답 사이)에서 접지 않는다(#48 · AI#1353). gold(수능 교재 정답 상자)는
#   쌍 사이에서만 접는데, 어절 접기가 32칸 안 마지막 빈칸을 고르면 `5` / `③  6 ②` 처럼 쌍이 갈렸다. 줄 끝까지 `번호 답`
#   토막이 번갈아 이어지고 번호가 1씩 늘고 원문자 답(①~⑤)이 하나 이상일 때만 그 쌍 안 빈칸을 자를 자리에서 뺀다.
#   앞에 붙은 글(상자 제목)은 둔다. 수학 선택지 `① 1  ② 2` 는 원문자가 번호 자리라 안 걸린다. AI 쪽 `breaks` 도 같은 판정이다(AI#1360).
_CIRCLED = ("⠼⠂", "⠼⠆", "⠼⠒", "⠼⠲", "⠼⠢")      # ①~⑤


def _is_num(tok: str) -> bool:
    return len(tok) > 1 and tok[0] == "⠼" and all(c in _DIGIT_CELLS for c in tok[1:])


def _pair_gaps(line: str) -> set:
    toks, i = [], 0
    while i < len(line):                      # 빈칸으로 가른 토막의 (시작, 끝)
        if line[i] == SPACE:
            i += 1
            continue
        j = i
        while j < len(line) and line[j] != SPACE:
            j += 1
        toks.append((i, j))
        i = j
    for s in range(len(toks) % 2, len(toks) - 3, 2):   # 줄 끝까지 이어지는 꼬리 — 가장 긴 것부터
        nums, anss = toks[s::2], toks[s + 1::2]
        if not all(_is_num(line[a:b]) for a, b in nums):
            continue
        if not all(_is_num(line[a:b]) or line[a:b] in _CIRCLED for a, b in anss):
            continue
        if not any(line[a:b] in _CIRCLED for a, b in anss):
            continue
        nos = [int("".join(str(_DIGIT_CELLS.index(c)) for c in line[a + 1:b])) for a, b in nums]
        if any(y != x + 1 for x, y in zip(nos, nos[1:])):
            continue
        return {k for (_, e), (a, _) in zip(nums, anss) for k in range(e, a)}
    return set()


def _wrap(line: str, cols: int) -> list[str]:
    """`cols`를 넘으면 **빈칸(어절) 자리에서** 자른다. 어절 하나가 폭보다 길면 그때만 강제 분리.

    종전에는 자리를 안 보고 `line[i:i + cols]`로 잘랐다. 그러면 한글 한 음절을 이루는
    점형이 두 줄로 갈린다 — 「점자 자료 제작 지침」 §2.1.1(2)가 원칙으로 삼는 **음절 단위
    줄바꿈**도, 예외로 허용하는 **어절 단위**도 아닌 값이다. 2026-09-08 대표 지적 ③에서
    사회학습지 예시 제목 '민주주의'가 `⠑⠟⠨⠍⠨` / `⠍⠺`로 갈려 나왔다.

    셀만 보고는 음절 경계를 알 수 없다(초성·종성 점형을 되짚어야 한다). 빈칸 경계는
    음절 경계의 부분집합이라 **음절을 쪼갤 일이 없고**, 정답 도서 실측도 어절이다
    (원장 C-83: 31칸 이상 줄이 gold dev 23.8%·val 24.9%). 지침 §2.1.1(2)의 예외절이
    "시험 문제지"를 집는데 우리 입력이 그것이다.
    """
    if not line:
        return [""]
    out: list[str] = []
    while len(line) > cols:
        gaps = _pair_gaps(line)
        cut = next((k for k in range(cols, -1, -1) if line[k] == SPACE and k not in gaps), -1)
        if cut <= 0 or not line[:cut].strip(SPACE):
            out.append(line[:cols])          # 어절 하나가 폭을 넘는다 — 그 자리에서만 강제 분리
            line = line[cols:]
        else:
            out.append(line[:cut].rstrip(SPACE))
            line = line[cut:].lstrip(SPACE)  # 자른 자리의 빈칸은 줄머리로 넘기지 않는다
    out.append(line)
    return out


def wrap(line: str, cols: int = 32, mode: str = "syllable",
         breaks: list | None = None, center: bool = False) -> list:
    """논리 줄 하나를 `cols` 칸 줄들로 접는다. 줄바꿈 두 갈래(2026-10-10 대표 확정, 기본 음절).

    syllable — `breaks`(그 셀 앞에서 끊어도 되는 자리, **이 줄 기준** 오프셋) 가운데 `cols` 칸 안에서 가장 먼
      자리에서 끊는다. 그런 자리가 없으면 `cols` 칸째에서 강제로 자르되 점역자 주 표 `⠠⠄` 는 가르지 않는다.
      끊은 자리 앞뒤 빈칸(줄 끝 · 이어지는 줄 머리)은 버린다. `docs/sidecar.md` §5 `fold` 와 같은 셈이다(엔진 조판과 39,562요소 같음).
      `breaks` 가 비면(옛 응답 · 점자를 직접 고친 요소 · 끊을 자리가 없는 줄) `word` 로 접는다(설계 §6-1).
    word — 빈칸(어절) 자리에서 자른다(`_wrap`, #9 · 원장 C-83).
    center — 1단계 제목. `cols` 를 넘어 접힌 줄만 조각마다 가운데에 놓는다.
      안 접힌 줄은 AI 가 이미 가운데 여백을 넣어 보낸다.
    """
    if mode not in WRAP_MODES:
        raise ValueError(f"wrap은 syllable|word: {mode!r}")
    if mode == "word" or not breaks:
        out = _wrap(line, cols)
    else:
        out, start = [], 0
        while len(line) - start > cols:
            ok = [b for b in breaks if start < b <= start + cols]
            cut = max(ok) if ok else start + cols
            if not ok and line[cut - 1:cut + 1] == _TN_MARK:
                cut -= 1
            piece = line[start:cut]
            out.append(piece.rstrip(SPACE + " ") or piece)    # 줄 끝 빈칸도 걷는다(어절 갈래 `_wrap` 과 같다, #72 E)
            start = cut
            while start < len(line) and line[start] in (SPACE, " "):
                start += 1
        if start < len(line) or not out:
            out.append(line[start:])
    if center and len(line) > cols:
        out = [SPACE * ((cols - len(s)) // 2) + s for s in out]
    return out


def _fold_blocks(blocks: list, opts: Options) -> list:
    """쪽바꿈 표식 사이 한 토막의 블록들을 이어 논리 줄로 나누고 `opts.wrap` 갈래로 접는다.

    블록 `breaks`(그 블록 `text` 기준, 응답 `contents[0]` 의 값 그대로)는 이은 문자열 기준으로 옮긴 뒤 줄마다
    그 줄의 시작 오프셋을 뺀다(sidecar.md §5 규칙 5). 줄 끝 · 줄 머리 자리는 안 쓴다(그 셀 앞에서 끊을 일이 없다).
    가운데 놓기(`heading_level` 1)는 그 줄이 시작하는 블록의 값을 쓴다.
    반환은 `(줄, 블록 align)` 이다. 정렬은 면을 나눈 뒤(점자 면 번호를 채운 뒤) 놓는다.
    """
    # 블록은 서로 다른 요소다. 끝 개행 없이 이으면 다음 블록 첫 줄과 한 줄로 붙는다(#40 · braille-assist#16,
    # 웹에서 저장한 쪽의 BE 다운로드). 빈 블록은 줄을 더하지 않고, 아래에서 토막 끝 개행을 종결자로 떼므로
    # 마지막 블록은 종전과 같다. `breaks` 는 그 블록 글 기준이라 끝에 붙인 개행이 오프셋을 안 흔든다.
    texts = [t if not t or t.endswith("\n") else t + "\n" for t in (b.get("text", "") for b in blocks)]
    seg = "".join(texts)
    if not seg:
        return []        # 내용이 아예 없는 토막(쪽바꿈 표식이 잇달은 자리)은 줄을 안 만든다
    starts, centers, aligns, gbreaks, acc = [], [], [], [], 0
    for b, t in zip(blocks, texts):
        starts.append(acc)
        centers.append(int(b.get("heading_level") or 0) == 1)
        al = b.get("align") or ""
        if al and al not in ALIGNS:
            raise ValueError(f"align은 left|center|right: {al!r}")
        aligns.append(al)
        gbreaks += [acc + x for x in (b.get("breaks") or [])]
        acc += len(t)
    # 통 문자열의 **끝 개행은 마지막 줄을 끝내는 종결자**이지 빈 줄이 아니다.
    # AI `flatten_elements`가 `suffix = "\n" * (after + 1)`로 내보내는데 그 +1이
    # 종결자다(docstring: "본문 마지막 줄을 끝내는 개행"). split("\n")은 그걸 빈
    # 줄로 세어 **원본 쪽마다 유령 빈 줄이 하나씩** 생겼다 — 변경선 바로 위에 늘
    # 빈 줄이 찍혔고, 쪽마다 한 줄씩 밀렸다. AI `_assemble_pages`는 안 그런다.
    if seg.endswith("\n"):
        seg = seg[:-1]
    out, base = [], 0
    for logical in seg.split("\n"):
        k = bisect_right(starts, base) - 1
        lb = [g - base for g in gbreaks if base < g < base + len(logical)]
        out += [(w, aligns[k]) for w in wrap(logical, opts.cols, opts.wrap, lb, centers[k])]
        base += len(logical) + 1
    return out


def _has_page_row(braille_page: int, on: str) -> bool:
    if on == "none":
        return False
    if on == "odd":
        return braille_page % 2 == 1
    if on == "even":
        return braille_page % 2 == 0
    return True


def _renumber(sources: list, opts: Options) -> list:
    """`orig_page_start`가 있으면 원본 페이지 번호를 다시 매긴다.

    표지(`cover_pages`개)는 준 번호를 그대로 두고, 그 뒤 n번째 본문 원본 페이지에
    `orig_page_start + n`을 붙인다. None이면 아무것도 하지 않는다.
    """
    if opts.orig_page_start is None:
        return sources
    out = []
    for i, src in enumerate(sources):
        s = dict(src)
        if i >= opts.cover_pages:
            s["orig_page"] = opts.orig_page_start + (i - opts.cover_pages)
        out.append(s)
    return out


# 쪽바꿈 표식(2026-09-03, FE QA L-2). 편집 화면에서 Ctrl+Enter 로 끼워 넣는 **독립 요소**이고
# 본문은 이 한 줄뿐이다. 조판에서 만나면 요소를 버리고 그 자리에서 면을 끊는다.
# 원본 쪽 경계(orig_page)와 무관하게 쪽 한가운데에서도 올 수 있다.
PAGE_BREAK_TAG = "<!쪽바꿈>"
# flat 안에서 쪽바꿈 자리를 표시하는 내부 값. 점자 텍스트에는 못 나오는 문자를 쓴다.
_BREAK = "\x00brk"

# ── 조판 태그(V4 점자 태깅 목록표, #66) ─────────────────────────────────────────────
# 장바꿈: 쪽바꿈처럼 그 자리에서 면을 끊고, 다음 내용은 **홀수 면**에서 시작한다. 앞 내용이 홀수 면에서 끝났으면
#   다음 짝수 면을 비운다(「점자 도서 제작 지침」 용어 ⑫ 재추출 4534~4537행 · 「점자 자료 제작 지침」 용어 (16) 396행).
CHAPTER_TAG = "<!장바꿈>"
_CHAPTER = "\x00chp"
_MARKS = (_BREAK, _CHAPTER)
# 줄을 먹는 태그: 그 태그 하나뿐인 블록을 `cols` 폭 한 줄로 펼친다. (머리 셀, 채움 셀, 끝 셀).
#   목록표의 `×30` 은 32칸일 때의 채움 수다. 칸 수를 바꾸면 채움 수가 따라 바뀐다.
RULE_TAGS = {
    "<!상단줄>": ("", "⠉", ""), "<!중단줄>": ("", "⠒", ""), "<!하단줄>": ("", "⠤", ""),
    "<!상단굵은줄>": ("", "⠛", ""), "<!하단굵은줄>": ("", "⠶", ""),
    "<!표시작>": ("⠖", "⠒", "⠲"), "<!표중앙>": ("⠗", "⠒", "⠺"), "<!표끝>": ("⠓", "⠒", "⠚"),
    "<!표구분선>": ("", "⠐", ""),
    "<!표지시작>": ("⠿", "⠛", "⠿"), "<!표지세로>": ("⠿", SPACE, "⠿"), "<!표지끝>": ("⠿", "⠶", "⠿"),
}
# 쪽 번호 자리표시: 블록 글(translate 가 그대로 통과시킨 `cells`) 속에 남아 오고, 여기서 그 줄이 놓인 쪽의
#   번호(⠼ + 숫자)로 바꾼다. 묵자 쪽 번호는 그 줄의 원본 쪽, 점자 면 번호는 그 줄이 놓인 면(표지 면은 빈칸).
#   접기는 자리표시 글자 수(8)로 셈한 뒤 바꾸므로 줄이 폭을 넘지 않는다(번호는 8칸보다 짧다).
ORIG_PAGE_TAG = "<!묵자쪽번호>"
BRAILLE_PAGE_TAG = "<!점자면번호>"
# 정렬: 블록 칸 `align`. 그 블록 줄들의 빈칸을 걷고 시작 칸만 바꾼다(줄 수는 안 바뀐다). 없으면 받은 그대로다.
ALIGNS = ("left", "center", "right")


def rule_line(tag: str, cols: int = 32) -> str:
    """줄을 먹는 태그 → `cols` 폭 한 줄. 예: `<!표시작>` 32칸 = ⠖ + ⠒×30 + ⠲."""
    a, f, z = RULE_TAGS[tag]
    return a + f * (cols - len(a) - len(z)) + z


def _align(line: str, cols: int, how: str) -> str:
    if not how:
        return line
    s = line.strip(SPACE + " ")
    if not s or how == "left":
        return s
    pad = max(cols - len(s), 0)
    return SPACE * (pad // 2 if how == "center" else pad) + s


def _fill_page_no(line: str, num: str) -> str:
    """점자 면 번호 자리표시를 채운다. 표지 면(번호 없음)에서 비우면 줄 끝에 남는 빈칸을 걷는다."""
    if BRAILLE_PAGE_TAG not in line:
        return line
    line = line.replace(BRAILLE_PAGE_TAG, num)
    return line if num else line.rstrip(SPACE)


def _header_line(text: str, orig_page: int, num: str, cols: int) -> str:
    """머리말 한 줄. 자리표시를 채우고 가운데에 놓는다(꼬리말 가운데와 같은 올림 셈). 넘치면 뒤를 자른다."""
    t = text.replace(BRAILLE_PAGE_TAG, num).replace(ORIG_PAGE_TAG, _number(orig_page)).strip(SPACE + " ")[:cols]
    return SPACE * ((cols - len(t) + 1) // 2) + t


def build_pages(
    sources: list,
    footer: str = "",
    start_braille_page: int = 1,
    opts: Options = DEFAULT,
    footers: dict | None = None,
    header: str = "",
    headers: dict | None = None,
) -> list:
    """원본 쪽별 통 문자열 → **완성된 점자 면 배열**. BRF 변환 직전 상태다.

    sources — `[{"orig_page": int, "blocks": [{"order": int, "text": str, "breaks": [int], "heading_level": int}]}]`
      · `text`는 ProcessPage가 낸 통 문자열(조판성 줄바꿈은 `\n`으로 들어 있다)
      · `blocks`는 `order`로 정렬해 이어 붙인다
      · `breaks`(선택)는 응답 `breaks` 그대로(그 블록 `text` 기준). 없으면 그 블록은 `word` 로 접는다
      · `heading_level`(선택)이 1이면 32칸을 넘어 접힌 줄을 가운데에 놓는다
    footer — 이미 점역된 꼬리말 점자(없으면 빈 문자열). 이 레포는 점역하지 않는다.
    footers — `{점자 면 번호: 꼬리말 점자}`. 그 면만 이 값을 쓰고, 없는 면은 `footer`를 쓴다.
      "이 면부터 끝까지 / 이 면만"은 **편집 시점의 뜻**이라 여기서 풀지 않는다.
      호출자(FE)가 범위를 해석해 면별 값으로 펼쳐 넘긴다(2026-09-01 결정 E).
    start_braille_page — 첫 면의 점자 면 번호. 표지 다음이 1이다(지침 1장2절2-3(1)).
    header · headers — 머리말(이미 점역됨). `footer` · `footers` 와 같은 꼴이다. 머리말이 있는 면은 첫 줄이
      머리말이고 본문이 한 줄 줄어든다. 표지 면과 장바꿈 · 짝수 면 채우기로 더한 빈 면에는 넣지 않는다.
      머리말이 없으면 면 나눔은 종전과 같다.

    반환 — 면 배열. 각 면은 줄 배열이고 길이는 `opts.rows`다. 페이지행이 들어가는 면은
    마지막 줄이 페이지행이고 본문이 `rows-1`줄이다.

    ★ 표지 판정은 `sources`의 **순번**이다 — 앞에서 `cover_pages`개가 표지다.
      쪽 번호로 보지 않는다(번호가 1부터가 아니거나 다시 매기면 어긋난다).
    ★ 페이지행의 원본 번호 = **그 면 첫 줄이 속한 원본 쪽**.
      지침 1장2절2-2(4) "점자 한 페이지에 원본 페이지 변경선이 2개 이상 나올 때에는
      해당 페이지에서 가장 먼저 나오는 원본 페이지 번호"와 같은 값이다.
      ⚠ 원장 **C-10**으로 자문 예정 — 면이 원본 쪽 중간에서 시작하면서 변경선이 2개 이상일 때
      두 해석이 갈릴 여지가 있다.
    ★ 걸침 순번(cont_idx) = 그 원본 쪽이 **처음 나온 면부터 센 순번**(0부터).
      지침 [예 1-7] 실물이 105·107·109면에 없음·b·d를 붙이는 근거다 — 페이지행이 홀수 면에만
      찍혀 a(106면)·c(108면)가 건너뛰어진 것이지 순번이 건너뛴 게 아니다.
    """
    # JSON을 거쳐 오면 키가 문자열이다("2"). 세 구현이 같게 굴도록 여기서 정수로 맞춘다.
    fmap = {int(k): v for k, v in (footers or {}).items()}
    hmap = {int(k): v for k, v in (headers or {}).items()}
    # 1) 원본 쪽 경계마다 변경선을 넣고 32칸으로 자른다. 줄마다 소속 원본 쪽을 들고 간다.
    sources = _renumber(sources, opts)
    # 원본 페이지 번호를 끄면 변경선은 ⠤만 남은 빈 줄이 된다 — 함께 끈다(결정 D).
    with_change = opts.show_change_line and opts.show_orig_page
    flat: list = []                       # (줄, 원본 쪽, 표지인가, 정렬)
    for i, src in enumerate(sources):
        op = int(src["orig_page"])
        # ★ 표지 판정은 **순번**이다(2026-09-01 결정 C). 종전에는 `쪽 번호 <= cover_pages`로
        #   봤는데, 번호가 1부터 시작하지 않거나 orig_page_start로 다시 매기면 어긋난다.
        cover = i < opts.cover_pages
        if i > 0 and with_change:         # 첫 원본 쪽 앞에는 변경선을 두지 않는다
            flat.append((page_change_line(op, opts), op, cover, ""))
        blocks = sorted(src.get("blocks") or [], key=lambda b: b.get("order", 0))
        # 쪽바꿈 · 장바꿈 표식에서 토막을 낸다. 표식이 없으면 종전과 똑같이 한 토막이다.
        segs: list = []
        cur: list = []
        for b in blocks:
            t = b.get("text", "").strip()
            if t in (PAGE_BREAK_TAG, CHAPTER_TAG):
                segs.append(cur)
                segs.append(_BREAK if t == PAGE_BREAK_TAG else _CHAPTER)
                cur = []
            elif t in RULE_TAGS:
                cur.append({"text": rule_line(t, opts.cols)})   # 폭이 꼭 cols 라 안 접힌다
            else:
                cur.append(b)
        segs.append(cur)
        for seg in segs:
            if isinstance(seg, str):
                flat.append((seg, op, cover, ""))
                continue
            for w, al in _fold_blocks(seg, opts):
                flat.append((w.replace(ORIG_PAGE_TAG, _number(op)), op, cover, al))

    # 2) 면으로 나눈다. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다.
    #
    # ★ 면 첫 줄의 빈 줄은 **버리지 않는다** — 지침 2장2절2 2)(3)(도서 906행)·§2.4.4(3)
    #   (자료 942행) "본문 사이의 빈 줄이 점자 페이지 처음에 위치하더라도 빈 줄을 삭제하지
    #   않는다". 2025 개정 요약 3(도서 145행)이 종전 예외를 없앤 자리다. AI 쪽
    #   `layout_braille._paginate`는 이미 규정대로다(2026-08-08 대표 결정, gold 3.2%).
    #   다만 **문서 맨 앞** 빈 줄은 '본문 사이'가 아니라 버린다.
    pages: list = []
    first_seen: dict = {}                 # 원본 쪽 → 그 쪽이 처음 나온 면 번호(0-based)
    last = -1                             # 마지막 내용 줄 — 뒤쪽 빈 줄로 빈 면을 만들지 않는다
    for k, (ln, *_r) in enumerate(flat):
        if ln not in _MARKS and ln.strip():
            last = k
    pos = 0
    while pos <= last and flat[pos][0] not in _MARKS and not flat[pos][0].strip():
        pos += 1                          # 문서 맨 앞의 빈 줄만 버린다

    def blank(bp: int, head_page: int, cover: bool) -> list:
        """빈 면(장바꿈 · 짝수 면 채우기). 페이지행은 다른 면과 같은 규칙이고 원본 번호는 앞 내용의 원본 쪽을 잇는다."""
        has_row = _has_page_row(bp, opts.page_row_on) and not cover
        body = [""] * (opts.rows - (1 if has_row else 0))
        if has_row:
            idx = len(pages)
            body.append(page_row(head_page, idx - first_seen.get(head_page, idx), bp, fmap.get(bp, footer), opts))
        return body

    bpn = start_braille_page              # 표지 면은 점자 면 번호를 소비하지 않는다
    need_odd = False                      # 장바꿈 뒤 — 다음 내용은 홀수 면에서 시작한다
    prev_op = None                        # 마지막으로 실은 줄의 원본 쪽(장바꿈 빈 면의 페이지행)
    while pos <= last:
        while pos <= last and flat[pos][0] in _MARKS:
            need_odd = need_odd or flat[pos][0] == _CHAPTER
            pos += 1                      # 이미 이룬 쪽바꿈 · 장바꿈 표식만 버린다
        if pos > last:
            break
        # 표지 범위 안이면 페이지행을 생략한다(조판 옵션 §5).
        on_cover = flat[pos][2]
        if need_odd and not on_cover and bpn % 2 == 0:
            pages.append(blank(bpn, flat[pos][1] if prev_op is None else prev_op, False))
            bpn += 1
        need_odd = False
        idx = len(pages)
        bp = bpn
        head_page = flat[pos][1]
        has_row = _has_page_row(bp, opts.page_row_on) and not on_cover
        head = "" if on_cover else hmap.get(bp, header)
        cap = opts.rows - (1 if has_row else 0) - (1 if head else 0)
        if cap < 1:
            raise ValueError(f"rows {opts.rows}줄에서 머리말 · 페이지행을 빼면 본문 줄이 남지 않는다")
        # 표식을 만나면 거기서 면을 끊는다 — 남은 칸은 아래에서 빈 줄로 채운다.
        end = pos
        while end < len(flat) and end - pos < cap and flat[end][0] not in _MARKS:
            end += 1
        num = "" if on_cover else _number(bp)
        body = [_align(_fill_page_no(ln, num), opts.cols, al) for ln, _o, _c, al in flat[pos:end]]
        prev_op = flat[end - 1][1]
        pos = end
        if pos < len(flat) and flat[pos][0] in _MARKS:
            need_odd = flat[pos][0] == _CHAPTER
            pos += 1                      # 표식 자체는 본문에 안 싣는다
        first_seen.setdefault(head_page, idx)
        body += [""] * (cap - len(body))
        if head:
            body.insert(0, _header_line(head, head_page, num, opts.cols))
        if has_row:
            f = fmap.get(bp, footer)
            body.append(page_row(head_page, idx - first_seen[head_page], bp, f, opts))
        if not on_cover:
            bpn += 1                      # 지침 1장2 3)(1)·§2.1.5(1): 표지 다음 면이 1이다
        pages.append(body)
    if opts.pad_to_even and len(pages) % 2 == 1:
        pages.append(blank(bpn, flat[last][1], flat[last][2]))
    return pages


# ── 조판 job 진입점 (V4 엔진 가이드 build_brf, 2026-10-14) ─────────────────────────
#
#   {"sources": [{"orig_page": 1,
#                 "blocks": [{"order": 0, "braille": "…", "breaks": [int, …]}, …]}, …],
#    "footer": "…",                 # 문서 기본 꼬리말(이미 점역됨, 선택)
#    "footers": {"3": "…"},         # 면별 꼬리말(점자 면 번호 → 꼬리말, 선택)
#    "opts": {"cols": 32, "rows": 26, "wrap": "syllable|word", "footer_align": "left|center|right",
#             "first_braille_page": 1, "cover_orig_page_count": 0, "orig_page_first_no": null,
#             "page_row_pages": "odd|every", "show_orig_page": true, "show_braille_page": true,
#             "pad_to_even": false}}
#
# ★ `blocks` 는 `order` 로 정렬한다(없으면 배열 순서). `braille` 은 translate 의 `cells` 그대로,
#   `breaks` 는 translate 의 `breaks` 그대로다. 없으면 그 블록은 빈칸에서 접는다.
# ★ 들여쓰기 · 가운데 정렬 · 구조적 빈 줄은 이미 `braille` 에 들어 있다. 여기서 또 넣지 않는다.
#   `heading_level`(가이드 밖, 받기는 한다)이 1이면 32칸을 넘어 접힌 1단계 제목 조각을 가운데에 놓는다.
# ★ 원본 페이지 변경선은 `show_orig_page` 를 따른다(끄면 같이 꺼진다).
# ★ 종전 꼴(`pages` · `elements` · `options` · `footer_braille` · `start_braille_page`)은 받지 않는다.
_PAGE_ROW_PAGES = ("odd", "every")


def _opt_flag(o: dict, key: str, default: bool) -> bool:
    """참거짓 옵션. 없거나 null 이면 기본값. 문자열 `"false"` 는 `bool()` 로 켜지므로 받지 않는다(#73, 사이드카 `BAD_FIELD`)."""
    v = o.get(key)
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    raise ValueError(f"{key} 는 true · false 여야 한다: {v!r}")


def _opt_size(o: dict, key: str, default: int) -> int:
    """칸 · 줄 수. 없거나 null 이면 기본값. 정수가 아니거나 1 보다 작으면 받지 않는다(#73, 종전 `rows: 0` 은 조용히 26줄)."""
    v = o.get(key)
    if v is None:
        return default
    if isinstance(v, int) and not isinstance(v, bool) and v >= 1:
        return v
    raise ValueError(f"{key} 는 1 이상의 정수여야 한다: {v!r}")


def options_from_job(job: dict) -> Options:
    """조판 job 의 `opts` → `Options`(V4 가이드 이름)."""
    o = job.get("opts") or {}
    rows_on = str(o.get("page_row_pages") or "odd")
    if rows_on not in _PAGE_ROW_PAGES:
        raise ValueError(f"page_row_pages는 odd|every: {rows_on!r}")
    start = o.get("orig_page_first_no")
    return Options(
        cols=_opt_size(o, "cols", 32),
        rows=_opt_size(o, "rows", 26),
        show_orig_page=_opt_flag(o, "show_orig_page", True),
        show_braille_page=_opt_flag(o, "show_braille_page", True),
        page_row_on=rows_on,
        cover_pages=int(o.get("cover_orig_page_count") or 0),
        orig_page_start=None if start in (None, "") else int(start),
        footer_align=str(o.get("footer_align") or "center"),
        wrap=str(o.get("wrap") or "syllable"),
        pad_to_even=_opt_flag(o, "pad_to_even", False),
    )


def build_pages_from_job(job: dict) -> list:
    """조판 job → 점자 면 배열. `build_pages`의 얇은 어댑터다."""
    sources = [
        {
            "orig_page": int(src.get("orig_page", i + 1)),
            "blocks": [{"order": b.get("order", k), "text": b.get("braille", ""), "breaks": b.get("breaks") or [],
                        "heading_level": b.get("heading_level") or 0, "align": b.get("align") or ""}
                       for k, b in enumerate(src.get("blocks") or [])],
        }
        for i, src in enumerate(job.get("sources") or [])
    ]
    # 면별 꼬리말 · 머리말 — 키가 문자열로 올 수 있어(JSON) 정수로 맞춘다.
    raw = job.get("footers") or {}
    footers = {int(k): v for k, v in raw.items()} if raw else None
    rawh = job.get("headers") or {}
    headers = {int(k): v for k, v in rawh.items()} if rawh else None
    o = job.get("opts") or {}
    return build_pages(
        sources,
        footer=job.get("footer", "") or "",
        start_braille_page=int(o.get("first_braille_page") or 1),
        opts=options_from_job(job),
        footers=footers,
        header=job.get("header", "") or "",
        headers=headers,
    )


def build_brf(job: dict) -> str:
    """조판 job → **.brf 파일 내용**(BRF Braille ASCII, 줄바꿈 `\n`).

    BE는 이 문자열을 그대로 파일로 쓰면 된다. 점역은 하지 않는다 — 이미 점역된
    통 문자열을 조판만 한다.
    """
    return "\n".join(to_brf_ascii(line)
                      for page in build_pages_from_job(job)
                      for line in page)


def build_brf_file(job: dict, replaced=None) -> bytes:
    """조판 job → **.brf 파일 바이트**(현장 꼴: 줄 끝 `\r\n`, 쪽마다 끝에 `\x0c`, 소문자 BRF ASCII).

    면 나누기는 `build_pages_from_job` 과 같고, 바이트 꼴만 `semojum_braille.brf.serialize_brf` 를 따른다.
    `replaced`(Counter)를 주면 빈칸으로 바꾼 글자와 횟수를 채운다.
    """
    o = options_from_job(job)
    return serialize_brf(build_pages_from_job(job), rows=o.rows, cols=o.cols, replaced=replaced)
